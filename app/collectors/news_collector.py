"""
app/collectors/news_collector.py
================================
Autonomous press spot report extractor for national daily market roundups
(e.g., The Daily Star, Prothom Alo, Financial Express).
Extracts prices via deterministic regex patterns and routes through confidence dampeners.
"""

import json
import logging
import random
import re
import time
from datetime import date
from pathlib import Path
from typing import List, Optional
import httpx

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)

BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


class NewsCollector(BaseCollector):
    """Regex-driven press and newspaper market roundup extractor."""

    source_code = "PRESS_REPORT"
    source_name = "National Daily Press Spot Roundups"
    source_type = "press"
    reliability_score = 0.70  # Tier 3 press confidence scalar

    DEFAULT_LIVE_URL = "https://www.prothomalo.com/topic/%E0%A6%AC%E0%A6%BE%E0%A6%9C%E0%A6%BE%E0%A6%B0-%E0%A6%A6%E0%A6%B0"
    FALLBACK_LIVE_URLS = [
        "https://www.prothomalo.com/business",
        "https://www.ittefaq.com.bd/business",
    ]

    def __init__(
        self,
        live_url: Optional[str] = None,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        timeout_seconds: float = 12.0,
    ):
        self.live_url = live_url or self.DEFAULT_LIVE_URL
        self.fixture_path = fixture_path or (settings.fixtures_dir / "newspaper_market_briefs.json")
        self.target_date = target_date or date.today()
        self.timeout = timeout_seconds

    def _convert_num(self, text: str) -> Optional[float]:
        """Convert English or Bengali numeric string to float."""
        if not text:
            return None
        trans = text.translate(BN_TO_EN).strip()
        try:
            return float(trans)
        except ValueError:
            return None

    def _fetch_briefs(self) -> tuple[List[dict], bool, float, Optional[str]]:
        """
        Actively harvest market desk articles from Prothom Alo and Ittefaq,
        extracting real paragraphs and quotations with automatic fixture fallback.
        Returns: (briefs_list, is_fallback, latency_ms, error_msg)
        """
        from bs4 import BeautifulSoup
        start_time = time.perf_counter()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        harvested_briefs: List[dict] = []
        candidate_urls = [self.live_url] + [u for u in self.FALLBACK_LIVE_URLS if u != self.live_url]

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                for hub_url in candidate_urls:
                    try:
                        r = client.get(hub_url, headers=headers)
                        if r.status_code != 200:
                            continue
                        soup = BeautifulSoup(r.text, "html.parser")
                        # 1. Collect article links
                        article_links = []
                        for a in soup.find_all("a"):
                            h = a.get("href", "")
                            if any(k in h for k in ["/business/", "/bangladesh/"]) and h not in article_links:
                                full_link = h if h.startswith("http") else "https://www.prothomalo.com" + h
                                article_links.append(full_link)

                        # 2. Extract price snippets directly from headlines/lead texts
                        lead_snippets = []
                        for el in soup.find_all(["h1", "h2", "h3", "p"]):
                            txt = el.get_text(strip=True)
                            if len(txt) > 10 and any(k in txt for k in ["টাকা", "টাকায়", "কেজি", "লিটার", "দাম"]):
                                lead_snippets.append(txt)

                        if lead_snippets:
                            source_tag = "Prothom Alo Market Desk" if "prothomalo" in hub_url else "Daily Ittefaq Business"
                            harvested_briefs.append({
                                "publication": source_tag,
                                "date": str(self.target_date),
                                "market_mention": "Karwan Bazar",
                                "text_snippets": lead_snippets[:15],
                            })

                        # 3. Deep-fetch up to 3 live market articles for detailed spot quotations
                        for art_link in article_links[:3]:
                            try:
                                art_r = client.get(art_link, headers=headers)
                                if art_r.status_code == 200:
                                    art_soup = BeautifulSoup(art_r.text, "html.parser")
                                    body_paras = [
                                        p.get_text(strip=True)
                                        for p in art_soup.find_all("p")
                                        if any(k in p.get_text() for k in ["টাকা", "টাকায়"])
                                        and any(c in p.get_text() for c in ["তেল", "চাল", "ডাল", "আলু", "পেঁয়াজ", "পেঁয়াজ", "মুরগি", "ডিম", "আটা", "ময়দা", "মাছ"])
                                    ]
                                    if body_paras:
                                        harvested_briefs.append({
                                            "publication": "Prothom Alo Market Report",
                                            "date": str(self.target_date),
                                            "market_mention": "Karwan Bazar",
                                            "text_snippets": body_paras[:8],
                                        })
                            except Exception:
                                pass

                    except Exception as e:
                        logger.debug(f"News hub harvest error on {hub_url}: {e}")

                if harvested_briefs:
                    latency_ms = (time.perf_counter() - start_time) * 1000.0
                    source_health_service.record_attempt(
                        source_code=self.source_code,
                        latency_ms=latency_ms,
                        success=True,
                        is_fallback=False,
                    )
                    return harvested_briefs, False, latency_ms, None
        except Exception as exc:
            logger.info(f"News live harvester failed, falling back to cached briefs: {exc}")

        # Fallback to structured fixture
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        if self.fixture_path.exists():
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=True,
                is_fallback=True,
            )
            return data, True, latency_ms, None

        return [], True, latency_ms, "Missing fixture"

    VALID_UNITS = {"কেজি", "হালি", "লিটার", "ডজন", "গ্রাম", "পিস", "kg", "pc"}

    def _sanitize_unit(self, unit_str: Optional[str]) -> str:
        if not unit_str:
            return "কেজি"
        u = unit_str.strip().lower()
        if "liter" in u or "লিটার" in u or "ltr" in u:
            return "লিটার"
        if "হালি" in u or "hali" in u:
            return "হালি"
        if "ডজন" in u or "dozen" in u:
            return "ডজন"
        if "kg" in u or "কেজি" in u:
            return "কেজি"
        if "pc" in u or "পিস" in u or "piece" in u:
            return "pc"
        return "কেজি"

    def parse_snippet(self, text: str, default_market: str) -> Optional[RawObservation]:
        """
        Apply deterministic regex rules to extract commodity, unit, and price quotation.
        """
        # Rule 1: Bengali range: "দেশি পেঁয়াজ বিক্রি হচ্ছে প্রতি কেজি ১২০ থেকে ১৩০ টাকায়"
        bn_range = re.search(
            r"([^\s।,]+(?:\s+[^\s।,]+)?)\s+(?:বিক্রি\s+হচ্ছে|দরে\s+বিক্রি|দাম)\s+(?:প্রতি)?\s*([^\s।,]+)?\s*([০-৯]+)\s*(?:থেকে|-|–)\s*([০-৯]+)\s*টাকা",
            text,
        )
        if bn_range:
            raw_name = bn_range.group(1).strip()
            raw_unit = self._sanitize_unit(bn_range.group(2))
            p1 = self._convert_num(bn_range.group(3))
            p2 = self._convert_num(bn_range.group(4))
            if p1 and p2:
                avg_price = round((p1 + p2) / 2.0, 2)
                return RawObservation(
                    source_code=self.source_code,
                    market_name=default_market,
                    raw_commodity_name=raw_name,
                    raw_unit=raw_unit,
                    raw_price=avg_price,
                    price_type="retail_avg",
                    observation_date=self.target_date,
                    completeness_score=0.85,
                    is_fallback=False,
                )

        # Rule 2: Bengali single/hyphen price: "নতুন আলু প্রতি কেজি ৫৫-৬০ টাকা"
        bn_single = re.search(
            r"([^\s।,]+(?:\s+[^\s।,]+)?)\s+প্রতি\s*([^\s।,]+)\s*([০-৯]+)(?:\s*[-–]\s*([০-৯]+))?\s*টাকা",
            text,
        )
        if bn_single:
            raw_name = bn_single.group(1).strip()
            raw_unit = self._sanitize_unit(bn_single.group(2))
            p1 = self._convert_num(bn_single.group(3))
            p2 = self._convert_num(bn_single.group(4)) if bn_single.group(4) else p1
            if p1 and p2:
                avg_price = round((p1 + p2) / 2.0, 2)
                return RawObservation(
                    source_code=self.source_code,
                    market_name=default_market,
                    raw_commodity_name=raw_name,
                    raw_unit=raw_unit,
                    raw_price=avg_price,
                    price_type="retail_avg",
                    observation_date=self.target_date,
                    completeness_score=0.85,
                    is_fallback=False,
                )

        # Rule 3: Headline pattern with price first or middle: "২২০০ টাকা কেজি ইলিশ" or "সয়াবিন তেলের দাম হয় ২০৪ টাকা"
        bn_headline_inverted = re.search(
            r"([০-৯]+(?:\.[০-৯]+)?|\d+(?:\.\d+)?)\s*টাকা\s*(?:কেজি|লিটার|হালি)?\s*([^\s।,]+(?:\s+[^\s।,]+)?)",
            text,
        )
        if bn_headline_inverted:
            p_val = self._convert_num(bn_headline_inverted.group(1))
            raw_name = bn_headline_inverted.group(2).strip()
            unit_guess = "লিটার" if "তেল" in raw_name or "লিটার" in text else ("pc" if "ডিম" in raw_name or "হালি" in text else "কেজি")
            if p_val and p_val > 10 and len(raw_name) > 1 and not any(k in raw_name for k in ["বেশি", "কম", "কমেছে", "বাড়তি", "কারণ", "বাজার"]):
                return RawObservation(
                    source_code=self.source_code,
                    market_name=default_market,
                    raw_commodity_name=raw_name,
                    raw_unit=unit_guess,
                    raw_price=p_val,
                    price_type="retail_avg",
                    observation_date=self.target_date,
                    completeness_score=0.85,
                    is_fallback=False,
                )

        # Rule 4: Verb pattern: "বোতলজাত সয়াবিন তেলের দাম হয় ২০৪ টাকা" or "খোলা আটা ৫০ টাকায় বিক্রি হচ্ছে"
        bn_verb_pattern = re.search(
            r"([^\s।,]+(?:\s+[^\s।,]+)?)\s+(?:দাম\s+হয়|দাম\s+দাঁড়িয়েছে|বিক্রি\s+হচ্ছে)\s+([০-৯]+|\d+)\s*টাকা",
            text,
        )
        if bn_verb_pattern:
            raw_name = bn_verb_pattern.group(1).strip()
            p_val = self._convert_num(bn_verb_pattern.group(2))
            unit_guess = "লিটার" if "তেল" in raw_name else ("pc" if "ডিম" in raw_name else "কেজি")
            if p_val and p_val > 10 and len(raw_name) > 1 and not any(k in raw_name for k in ["টিসিবি", "সরকার"]):
                return RawObservation(
                    source_code=self.source_code,
                    market_name=default_market,
                    raw_commodity_name=raw_name,
                    raw_unit=unit_guess,
                    raw_price=p_val,
                    price_type="retail_avg",
                    observation_date=self.target_date,
                    completeness_score=0.85,
                    is_fallback=False,
                )

        # Rule 5: English quotation: "local onion quoted at Tk 120-130 per kg"
        en_quote = re.search(
            r"([a-zA-Z\s]+?)\s+(?:quoted at|retailing between|selling at|sold at)\s+(?:Tk\.?|BDT)?\s*(\d+(?:\.\d+)?)\s*(?:to|-|and)\s*(\d+(?:\.\d+)?)\s*(?:per|\/)\s*([a-zA-Z]+)",
            text,
            re.IGNORECASE,
        )
        if en_quote:
            raw_name = en_quote.group(1).strip()
            p1 = float(en_quote.group(2))
            p2 = float(en_quote.group(3))
            raw_unit = en_quote.group(4).strip().lower()
            avg_price = round((p1 + p2) / 2.0, 2)
            return RawObservation(
                source_code=self.source_code,
                market_name=default_market,
                raw_commodity_name=raw_name,
                raw_unit=raw_unit,
                raw_price=avg_price,
                price_type="retail_avg",
                observation_date=self.target_date,
                completeness_score=0.85,
                is_fallback=False,
            )

        return None

    def collect(self) -> List[RawObservation]:
        """Harvest press spot report observations."""
        articles, is_fallback, _, _ = self._fetch_briefs()
        observations: List[RawObservation] = []

        for article in articles:
            market = article.get("market_mention", "Karwan Bazar")
            for snippet in article.get("text_snippets", []):
                obs = self.parse_snippet(snippet, default_market=market)
                if obs:
                    obs.is_fallback = is_fallback
                    observations.append(obs)

        logger.info(f"News Collector extracted {len(observations)} price mentions from press briefs.")
        return observations
