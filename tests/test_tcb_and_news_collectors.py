"""
tests/test_tcb_and_news_collectors.py
======================================
Verifies autonomous harvesters for TCB daily bulletin and Press spot reports:
- HTML tabular parsing and Bengali numeral conversion in TCBCollector
- Deterministic regex extraction across Bengali and English market sentences in NewsCollector
- Graceful offline fallback resilience
- Telemetry logging in SourceHealthService
"""

import pytest
from unittest.mock import patch

from app.collectors.base import RawObservation
from app.collectors.tcb_collector import TCBCollector
from app.collectors.news_collector import NewsCollector
from app.services.source_health import source_health_service


class TestTCBCollector:
    """Validate TCB bulletin ingestion and fallback."""

    def test_tcb_collector_harvest(self):
        collector = TCBCollector()
        items = collector.collect()
        assert isinstance(items, list)
        assert len(items) >= 5

        for obs in items:
            assert isinstance(obs, RawObservation)
            assert obs.source_code == "TCB_DAILY"
            assert obs.raw_price > 0
            assert obs.raw_unit in ["কেজি", "লিটার", "হালি", "kg", "pc"]
            assert obs.price_type == "retail_avg"

    def test_tcb_numeral_conversion(self):
        collector = TCBCollector()
        assert collector._convert_bn_number("১২০") == 120.0
        assert collector._convert_bn_number("১১০-১২০") == 115.0
        assert collector._convert_bn_number("৭৫০-৭৮০") == 765.0
        assert collector._convert_bn_number("") is None

    def test_tcb_fallback_resilience(self):
        with patch("httpx.Client.get", side_effect=Exception("Network down")):
            collector = TCBCollector()
            items = collector.collect()
            assert len(items) > 0
            assert any(item.is_fallback for item in items)


class TestNewsCollector:
    """Validate press spot report regex extraction."""

    def test_news_collector_harvest(self):
        collector = NewsCollector()
        items = collector.collect()
        assert isinstance(items, list)
        assert len(items) >= 4

        for obs in items:
            assert isinstance(obs, RawObservation)
            assert obs.source_code == "PRESS_REPORT"
            assert obs.raw_price > 0
            assert obs.raw_unit in ["কেজি", "হালি", "লিটার", "kg", "pc"]

    def test_bengali_sentence_parsing(self):
        collector = NewsCollector()
        sentence = "রাজধানীর কারওয়ান বাজারে আজ দেশি পেঁয়াজ বিক্রি হচ্ছে প্রতি কেজি ১২০ থেকে ১৩০ টাকায়।"
        obs = collector.parse_snippet(sentence, default_market="Karwan Bazar")
        assert obs is not None
        assert "পেঁয়াজ" in obs.raw_commodity_name
        assert obs.raw_price == 125.0
        assert obs.raw_unit == "কেজি"
        assert obs.market_name == "Karwan Bazar"

    def test_english_sentence_parsing(self):
        collector = NewsCollector()
        sentence = "At Mirpur-1 kitchen market, local onion quoted at Tk 120-130 per kg."
        obs = collector.parse_snippet(sentence, default_market="Mirpur-1 Kacha Bazar")
        assert obs is not None
        assert "onion" in obs.raw_commodity_name.lower()
        assert obs.raw_price == 125.0
        assert obs.raw_unit.lower() == "kg"

    def test_news_fallback_resilience(self):
        with patch("httpx.Client.get", side_effect=Exception("Connection timed out")):
            collector = NewsCollector()
            items = collector.collect()
            assert len(items) > 0


class TestSourceHealthIntegration:
    """Verify telemetry state transitions for newly integrated harvesters."""

    def test_tcb_source_registered(self):
        telemetry = source_health_service.get_source_telemetry("TCB_DAILY")
        assert telemetry is not None
        assert telemetry["source_code"] == "TCB_DAILY"

    def test_press_source_registered(self):
        telemetry = source_health_service.get_source_telemetry("PRESS_REPORT")
        assert telemetry is not None
        assert telemetry["source_code"] == "PRESS_REPORT"
