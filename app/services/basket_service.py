"""
Basket Optimization Service — core calculus engine for the Consumer Bazaar Basket feature.

Responsibilities:
  - Normalize customary units (হালি → 4 pc, পোয়া → 0.25 kg, মণ → 40 kg).
  - Pull today's wholesale, retail, and online prices per commodity via the DB.
  - Impute missing channel prices from cross-channel averages.
  - Compute 7-day trailing basket total and personal inflation shift.
  - Generate channel cost breakdowns, smart saving tips, and Bengali explanations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.commodity import Commodity
from app.models.location import Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.models.basket import SavedBasket, SavedBasketItem
from app.schemas.basket import (
    BasketCalculationRequest,
    BasketCalculationResponse,
    BasketItemCostDetail,
    BasketItemInput,
    ChannelCostBreakdown,
    SavedBasketCreate,
    SavedBasketDetailOut,
    SavedBasketItemOut,
    SavedBasketSummaryOut,
    BasketTrendPoint,
    BasketTrendResponse,
)
from app.services.normalizer import commodity_normalizer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal aggregation container
# ---------------------------------------------------------------------------

@dataclass
class _ChannelPrices:
    """Aggregated channel prices for a single commodity on a given date."""

    wholesale: Optional[float] = None
    retail: Optional[float] = None
    online: Optional[float] = None

    def overall_average(self) -> Optional[float]:
        """Return the mean across all available channels."""
        available = [p for p in (self.wholesale, self.retail, self.online) if p is not None]
        return round(sum(available) / len(available), 2) if available else None

    def benchmark(self) -> Optional[float]:
        """Best retail-side benchmark: retail → online → wholesale fallback."""
        return self.retail or self.online or self.wholesale


@dataclass
class _ItemCalc:
    """Intermediate calculation state for a single basket line-item."""

    commodity_id: int
    canonical_name: str
    bangla_name: str
    standard_unit: str
    quantity_normalized: float  # in base unit after unit normalization
    today_prices: _ChannelPrices = field(default_factory=_ChannelPrices)
    week_prices: _ChannelPrices = field(default_factory=_ChannelPrices)  # t-7 day prices


# ---------------------------------------------------------------------------
# Commodity close-variant map for smart saving tips
# ---------------------------------------------------------------------------

# Maps canonical commodity names to cheaper / substitute options with a tip
_SUBSTITUTE_TIPS: dict[str, tuple[str, str]] = {
    "Onion (Local)": (
        "Onion (Imported)",
        "দেশি পেঁয়াজের বিকল্প হিসেবে আমদানি পেঁয়াজ বিবেচনা করা যেতে পারে।",
    ),
    "Rice (Miniket)": (
        "Rice (Coarse)",
        "মিনিকেটের বদলে মোটা চাল নিলে উল্লেখযোগ্য সাশ্রয় সম্ভব।",
    ),
    "Soybean Oil (Bottled)": (
        "Soybean Oil (Loose)",
        "বোতলজাত সয়াবিনের বদলে খোলা সয়াবিন তেল নিলে সাশ্রয় হতে পারে।",
    ),
    "Deshi Chicken": (
        "Broiler Chicken",
        "দেশি মুরগির বদলে ব্রয়লার মুরগি নিলে উল্লেখযোগ্য সাশ্রয় সম্ভব।",
    ),
    "Rui Fish (Fresh)": (
        "Pangas Fish (Farm)",
        "রুই মাছের বদলে পাঙ্গাশ বা তেলাপিয়া মাছ বেছে নিলে খরচ অনেকটা কমে।",
    ),
}

# Channel display labels
_CHANNEL_LABELS = {
    "wholesale": "🏪 পাইকারি বাজার",
    "retail": "🛒 খুচরা বাজার",
    "online": "📱 অনলাইন / সুপারশপ",
}


class BasketOptimizationService:
    """
    Core engine that calculates the optimized cost breakdown for a user-supplied
    market basket across wholesale, retail, and online channels.
    """

    # ---------------------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------------------

    def calculate(
        self,
        request: BasketCalculationRequest,
        db: Session,
    ) -> BasketCalculationResponse:
        """
        Execute full basket optimization analysis.

        Steps:
          1. Resolve and normalize each item's unit to the canonical base unit.
          2. Query today's and 7-day-ago prices across all channels.
          3. Impute missing channel prices from available data.
          4. Aggregate channel totals and compute savings.
          5. Calculate 7-day personal inflation shift.
          6. Generate Bengali-language explanation and smart saving tips.
        """
        today = date.today()
        week_ago = today - timedelta(days=7)

        item_calcs: list[_ItemCalc] = []

        for item in request.items:
            commodity = db.get(Commodity, item.commodity_id)
            if not commodity:
                logger.warning("Basket: commodity_id=%d not found — skipping.", item.commodity_id)
                continue

            # Normalize user-supplied unit relative to commodity's canonical default unit
            comm_unit = (commodity.default_unit or "kg").lower()
            raw_u = item.raw_unit.strip().lower() if item.raw_unit else comm_unit

            if comm_unit in ("hali", "হালি"):
                if raw_u in ("hali", "হালি", "প্রতি হালি", "প্রতিহালি"):
                    quantity_normalized = item.quantity
                    base_unit = "hali"
                elif raw_u in ("pc", "pcs", "piece", "পিস", "টি", "টা"):
                    quantity_normalized = round(item.quantity / 4.0, 4)
                    base_unit = "hali"
                else:
                    try:
                        _, mult = commodity_normalizer.normalize_unit(item.raw_unit)
                        quantity_normalized = round(item.quantity * (mult / 4.0), 4)
                        base_unit = "hali"
                    except ValueError:
                        quantity_normalized = item.quantity
                        base_unit = comm_unit
            elif comm_unit in ("bundle", "আঁটি", "আটি"):
                quantity_normalized = item.quantity
                base_unit = "bundle"
            else:
                try:
                    base_unit, multiplier = commodity_normalizer.normalize_unit(item.raw_unit)
                    quantity_normalized = round(item.quantity * multiplier, 4)
                except ValueError:
                    logger.warning(
                        "Basket: unrecognized unit '%s' for commodity %d — using raw quantity.",
                        item.raw_unit,
                        item.commodity_id,
                    )
                    base_unit = commodity.default_unit
                    quantity_normalized = item.quantity

            calc = _ItemCalc(
                commodity_id=commodity.id,
                canonical_name=commodity.canonical_name,
                bangla_name=commodity.bangla_name,
                standard_unit=base_unit,
                quantity_normalized=quantity_normalized,
            )

            # Pull prices for today and 7 days ago
            calc.today_prices = self._fetch_channel_prices(db, commodity.id, today)
            calc.week_prices = self._fetch_channel_prices(db, commodity.id, week_ago)

            # Impute if channel data is missing (use overall average as benchmark)
            self._impute_missing(calc.today_prices)
            self._impute_missing(calc.week_prices)

            item_calcs.append(calc)

        if not item_calcs:
            # Empty basket after resolution — return a zeroed response
            return self._empty_response()

        # ---------------------------------------------------------------------------
        # Aggregate channel totals
        # ---------------------------------------------------------------------------

        wholesale_total = 0.0
        retail_total = 0.0
        online_total = 0.0
        benchmark_total = 0.0
        week_total = 0.0

        item_details: list[BasketItemCostDetail] = []

        for calc in item_calcs:
            prices = calc.today_prices
            qty = calc.quantity_normalized

            # Retail benchmark for this item
            benchmark_price = self._clean_price(prices.benchmark() or 0.0)
            line_benchmark = self._clean_price(benchmark_price * qty) or 0.0
            benchmark_total += line_benchmark

            # Channel line totals (fall back to benchmark if channel absent)
            wh_price = self._clean_price(prices.wholesale or benchmark_price)
            re_price = self._clean_price(prices.retail or benchmark_price)
            on_price = self._clean_price(prices.online or benchmark_price)

            wholesale_total += self._clean_price(wh_price * qty) or 0.0
            retail_total += self._clean_price(re_price * qty) or 0.0
            online_total += self._clean_price(on_price * qty) or 0.0

            # 7-day ago total (for inflation shift)
            week_bench = self._clean_price(calc.week_prices.benchmark() or benchmark_price)
            week_total += self._clean_price(week_bench * qty) or 0.0

            item_details.append(
                BasketItemCostDetail(
                    commodity_id=calc.commodity_id,
                    canonical_name=calc.canonical_name,
                    bangla_name=calc.bangla_name,
                    quantity_normalized=round(qty, 3),
                    standard_unit=calc.standard_unit,
                    unit_price=benchmark_price,
                    line_total=line_benchmark,
                    channel_prices={
                        "wholesale": wh_price,
                        "retail": re_price,
                        "online": on_price,
                    },
                )
            )

        # Round totals
        wholesale_total = round(wholesale_total, 2)
        retail_total = round(retail_total, 2)
        online_total = round(online_total, 2)
        benchmark_total = round(benchmark_total, 2)
        week_total = round(week_total, 2)

        # ---------------------------------------------------------------------------
        # Determine best channel and savings
        # ---------------------------------------------------------------------------

        channel_totals = {
            "wholesale": wholesale_total,
            "retail": retail_total,
            "online": online_total,
        }
        best_channel_key = min(channel_totals, key=lambda k: channel_totals[k])
        best_channel_label = _CHANNEL_LABELS[best_channel_key]
        best_total = channel_totals[best_channel_key]
        max_savings = round(benchmark_total - best_total, 2)

        # ---------------------------------------------------------------------------
        # Channel breakdown objects for response
        # ---------------------------------------------------------------------------

        channel_breakdowns: list[ChannelCostBreakdown] = []
        for key, label in _CHANNEL_LABELS.items():
            total = channel_totals[key]
            diff = round(total - benchmark_total, 2)
            diff_pct = round((diff / benchmark_total) * 100, 1) if benchmark_total > 0 else 0.0
            channel_breakdowns.append(
                ChannelCostBreakdown(
                    channel_name=label,
                    total_cost=total,
                    savings_vs_retail=round(-diff, 2),
                    difference_pct=diff_pct,
                )
            )

        # ---------------------------------------------------------------------------
        # 7-day cost shift
        # ---------------------------------------------------------------------------

        cost_shift_bdt = round(benchmark_total - week_total, 2)
        cost_shift_pct = (
            round(((benchmark_total - week_total) / week_total) * 100, 1)
            if week_total > 0
            else 0.0
        )

        # ---------------------------------------------------------------------------
        # Bengali savings explanation
        # ---------------------------------------------------------------------------

        savings_explanation = self._build_savings_explanation(
            best_channel_key=best_channel_key,
            wholesale_total=wholesale_total,
            online_total=online_total,
            benchmark_total=benchmark_total,
            wholesale_savings=round(benchmark_total - wholesale_total, 2),
            online_diff=round(online_total - benchmark_total, 2),
        )

        # ---------------------------------------------------------------------------
        # Smart saving tips & Empirical Cheaper Alternatives (Phase 5B)
        # ---------------------------------------------------------------------------

        smart_tips = self._generate_smart_tips(item_calcs, item_details)

        from app.services.alternative_service import alternative_service
        basket_tuples = [
            (calc.commodity_id, calc.quantity_normalized, calc.standard_unit)
            for calc in item_calcs
        ]
        alternatives = alternative_service.find_alternatives_for_basket(
            db=db,
            basket_items=basket_tuples,
            target_date=today,
            channel="retail",
        )

        return BasketCalculationResponse(
            benchmark_total=benchmark_total,
            wholesale_total=wholesale_total,
            retail_total=retail_total,
            online_total=online_total,
            best_channel=best_channel_label,
            max_savings_bdt=max_savings,
            savings_explanation=savings_explanation,
            cost_shift_7d_pct=cost_shift_pct,
            cost_shift_7d_bdt=cost_shift_bdt,
            item_details=item_details,
            smart_saving_tips=smart_tips,
            price_alternatives=alternatives,
        )

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def _clean_price(val: Optional[float]) -> Optional[float]:
        """Round consumer-facing prices to clean integers or realistic half-taka formats (e.g. 50.0, 52.5, 125.0)."""
        if val is None:
            return None
        half_rounded = round(val * 2) / 2.0
        return half_rounded if half_rounded != int(half_rounded) else float(int(half_rounded))

    def _fetch_channel_prices(
        self,
        db: Session,
        commodity_id: int,
        target_date: date,
    ) -> _ChannelPrices:
        """
        Fetch the most recent price observation for each channel within a 14-day
        window ending at target_date, prioritizing today's live DAM and TCB observations.
        """
        window_start = target_date - timedelta(days=14)

        # 1. Prioritize observations on target_date specifically (e.g. today's live DAM/TCB)
        rows_today = db.execute(
            select(
                PriceObservation.price_type,
                Market.market_type,
                Source.source_type,
                Source.code.label("source_code"),
                func.avg(PriceObservation.normalized_price).label("avg_price"),
            )
            .join(Market, PriceObservation.market_id == Market.id)
            .join(Source, PriceObservation.source_id == Source.id)
            .where(
                PriceObservation.commodity_id == commodity_id,
                PriceObservation.observation_date == target_date,
            )
            .group_by(
                PriceObservation.price_type,
                Market.market_type,
                Source.source_type,
                Source.code,
            )
        ).all()

        rows = rows_today
        if not rows:
            # 2. Fallback to 14-day historical window if no observation exists on target_date
            rows = db.execute(
                select(
                    PriceObservation.price_type,
                    Market.market_type,
                    Source.source_type,
                    Source.code.label("source_code"),
                    func.avg(PriceObservation.normalized_price).label("avg_price"),
                )
                .join(Market, PriceObservation.market_id == Market.id)
                .join(Source, PriceObservation.source_id == Source.id)
                .where(
                    PriceObservation.commodity_id == commodity_id,
                    PriceObservation.observation_date >= window_start,
                    PriceObservation.observation_date <= target_date,
                )
                .group_by(
                    PriceObservation.price_type,
                    Market.market_type,
                    Source.source_type,
                    Source.code,
                )
            ).all()

        channel = _ChannelPrices()
        wholesale_prices: list[float] = []
        retail_prices: list[float] = []
        online_prices: list[float] = []

        for row in rows:
            source_code = (row.source_code or "").upper()
            source_type = (row.source_type or "").lower()

            # Modeled, simulation, or isolated benchmarks must NEVER contaminate real market channel aggregates
            if source_code == "PANDAMART_MODELED" or source_type == "modeled_benchmark":
                continue

            price = float(row.avg_price)
            market_type = (row.market_type or "").lower()
            price_type = (row.price_type or "").lower()

            if (
                source_code in ("CHALDAL_RETAIL",)
                or source_type in ("retail_ecommerce",)
                or market_type == "online"
            ):
                online_prices.append(price)
            elif "wholesale" in price_type or market_type == "wholesale":
                wholesale_prices.append(price)
            else:
                retail_prices.append(price)

        if wholesale_prices:
            channel.wholesale = self._clean_price(sum(wholesale_prices) / len(wholesale_prices))
        if retail_prices:
            channel.retail = self._clean_price(sum(retail_prices) / len(retail_prices))
        if online_prices:
            channel.online = self._clean_price(sum(online_prices) / len(online_prices))

        return channel

    @staticmethod
    def _impute_missing(prices: _ChannelPrices) -> None:
        """
        Fill in missing channel prices using the overall average across available
        channels.  This ensures a full cost comparison even when only one channel
        has observations for a specific commodity.
        """
        avg = prices.overall_average()
        if avg is None:
            return
        if prices.wholesale is None:
            prices.wholesale = avg
        if prices.retail is None:
            prices.retail = avg
        if prices.online is None:
            # Online / super-shop typically carries a small premium
            prices.online = round(avg * 1.08, 2)

    @staticmethod
    def _build_savings_explanation(
        best_channel_key: str,
        wholesale_total: float,
        online_total: float,
        benchmark_total: float,
        wholesale_savings: float,
        online_diff: float,
    ) -> str:
        """Compose a consumer-friendly Bengali explanation of the savings opportunity."""
        wh_savings_str = f"৳{abs(wholesale_savings):.0f}"
        on_diff_str = f"৳{abs(online_diff):.0f}"

        if best_channel_key == "wholesale":
            return (
                f"পাইকারি বাজার থেকে কিনলে আপনার {wh_savings_str} বাঁচবে"
                + (
                    f", আর অনলাইন থেকে কিনলে {on_diff_str} বেশি লাগবে।"
                    if online_diff > 0
                    else "।"
                )
            )
        elif best_channel_key == "retail":
            return (
                f"এই বাজারের জন্য খুচরা বাজার সবচেয়ে সাশ্রয়ী। "
                f"পাইকারি থেকে {wh_savings_str} সাশ্রয় সম্ভব হলেও আজকের দরে খুচরা বাজারই লাভজনক।"
            )
        else:
            online_savings = round(benchmark_total - online_total, 2)
            return (
                f"অনলাইন / সুপারশপ থেকে কিনলে আপনার ৳{online_savings:.0f} বাঁচবে"
                + (
                    f", পাইকারি বাজারে {wh_savings_str} সাশ্রয় সম্ভব হলেও ডেলিভারির সুবিধায় অনলাইন লাভজনক।"
                    if wholesale_savings > 0
                    else "।"
                )
            )

    @staticmethod
    def _generate_smart_tips(
        item_calcs: list[_ItemCalc],
        item_details: list[BasketItemCostDetail],
    ) -> list[str]:
        """
        Formulate actionable procurement tips:
          1. Substitute suggestions for high-cost commodities.
          2. Bulk purchase recommendation for high-quantity items.
          3. General freshness/timing tip.
        """
        tips: list[str] = []
        commodity_names = {calc.commodity_id: calc.canonical_name for calc in item_calcs}

        # Substitute tip lookup
        for calc in item_calcs:
            name = calc.canonical_name
            if name in _SUBSTITUTE_TIPS:
                _, tip_text = _SUBSTITUTE_TIPS[name]
                tips.append(tip_text)
                if len(tips) >= 2:
                    break

        # Bulk purchase tip for items > 2 kg / 2 liter
        for calc in item_calcs:
            if calc.quantity_normalized >= 2.0 and calc.standard_unit in ("kg", "liter"):
                tips.append(
                    f"{calc.bangla_name} বেশি পরিমাণে কিনলে পাইকারি দরে সাশ্রয় বেশি হয়।"
                )
                break

        # Timing tip — always add one general tip
        tips.append("সপ্তাহের শুরুতে (শনি-রবিবার) বাজার করলে তাজা মালে ভালো দাম পাওয়া যায়।")

        # Limit to max 4 tips
        return tips[:4]

    @staticmethod
    def normalize_item(quantity: float, raw_unit: str) -> tuple[float, str]:
        """Normalize customary unit to base metric quantity and standard unit string."""
        try:
            base_unit, multiplier = commodity_normalizer.normalize_unit(raw_unit)
            return round(quantity * multiplier, 4), base_unit
        except ValueError:
            return quantity, raw_unit

    @staticmethod
    def _empty_response() -> BasketCalculationResponse:
        """Return a zeroed response for an empty or unresolvable basket."""
        return BasketCalculationResponse(
            benchmark_total=0.0,
            wholesale_total=0.0,
            retail_total=0.0,
            online_total=0.0,
            best_channel="🛒 খুচরা বাজার",
            max_savings_bdt=0.0,
            savings_explanation="বাস্কেটে কোনো পণ্য যোগ করা হয়নি।",
            cost_shift_7d_pct=0.0,
            cost_shift_7d_bdt=0.0,
            item_details=[],
            smart_saving_tips=[],
            price_alternatives=[],
        )

    # -----------------------------------------------------------------------
    # Saved Basket & Personal Inflation Tracking Methods
    # -----------------------------------------------------------------------

    def save_basket(self, db: Session, payload: SavedBasketCreate) -> SavedBasketDetailOut:
        """Persist a user's customized basket to SQLite and return calculation detail."""
        # Validate that all commodities exist
        commodity_ids = [item.commodity_id for item in payload.items]
        existing_comms = {
            c.id: c
            for c in db.scalars(select(Commodity).where(Commodity.id.in_(commodity_ids))).all()
        }
        for item in payload.items:
            if item.commodity_id not in existing_comms:
                raise ValueError(f"Commodity with ID {item.commodity_id} not found in taxonomy.")

        basket = SavedBasket(
            name=payload.name.strip(),
            bangla_name=payload.bangla_name.strip() if payload.bangla_name else None,
            description=payload.description.strip() if payload.description else None,
        )
        db.add(basket)
        db.flush()

        for item in payload.items:
            db_item = SavedBasketItem(
                basket_id=basket.id,
                commodity_id=item.commodity_id,
                quantity=float(item.quantity),
                unit=item.unit.strip(),
            )
            db.add(db_item)

        db.commit()
        db.refresh(basket)

        detail = self.get_saved_basket(db, basket.id)
        if not detail:
            raise ValueError("Failed to retrieve created basket.")
        return detail

    def list_saved_baskets(self, db: Session) -> list[SavedBasketSummaryOut]:
        """Return summary cards for all saved household baskets with live totals."""
        baskets = list(
            db.scalars(select(SavedBasket).order_by(SavedBasket.created_at.desc())).all()
        )
        summaries: list[SavedBasketSummaryOut] = []

        for b in baskets:
            if not b.items:
                continue

            calc_req = BasketCalculationRequest(
                items=[
                    BasketItemInput(
                        commodity_id=item.commodity_id,
                        quantity=item.quantity,
                        raw_unit=item.unit,
                    )
                    for item in b.items
                ]
            )
            calc_resp = self.calculate(request=calc_req, db=db)

            # Compute 30d shift
            cost_today = calc_resp.benchmark_total
            cost_30d = 0.0
            date_30d = date.today() - timedelta(days=30)
            for item in b.items:
                norm_q, _ = self.normalize_item(item.quantity, item.unit)
                ch_30d = self._fetch_channel_prices(db, item.commodity_id, date_30d)
                bench_30d = ch_30d.benchmark() or (calc_resp.benchmark_total / len(b.items))
                cost_30d += bench_30d * norm_q

            shift_30d_pct = (
                round(((cost_today - cost_30d) / cost_30d) * 100.0, 2)
                if cost_30d > 0
                else 0.0
            )

            summaries.append(
                SavedBasketSummaryOut(
                    id=b.id,
                    name=b.name,
                    bangla_name=b.bangla_name,
                    description=b.description,
                    item_count=len(b.items),
                    created_at=b.created_at.isoformat() if b.created_at else "",
                    updated_at=b.updated_at.isoformat() if b.updated_at else "",
                    current_retail_total=calc_resp.retail_total,
                    current_wholesale_total=calc_resp.wholesale_total,
                    current_online_total=calc_resp.online_total,
                    max_savings_bdt=calc_resp.max_savings_bdt,
                    best_channel=calc_resp.best_channel,
                    shift_7d_pct=calc_resp.cost_shift_7d_pct,
                    shift_30d_pct=shift_30d_pct,
                )
            )

        return summaries

    def get_saved_basket(self, db: Session, basket_id: int) -> Optional[SavedBasketDetailOut]:
        """Fetch a saved basket by ID with full item details and channel calculation."""
        basket = db.get(SavedBasket, basket_id)
        if not basket:
            return None

        calc_req = BasketCalculationRequest(
            items=[
                BasketItemInput(
                    commodity_id=item.commodity_id,
                    quantity=item.quantity,
                    raw_unit=item.unit,
                )
                for item in basket.items
            ]
        )
        calc_resp = self.calculate(request=calc_req, db=db)

        item_out_map = {d.commodity_id: d for d in calc_resp.item_details}
        detailed_items: list[SavedBasketItemOut] = []

        for db_item in basket.items:
            detail = item_out_map.get(db_item.commodity_id)
            c_name = detail.canonical_name if detail else f"Commodity #{db_item.commodity_id}"
            b_name = detail.bangla_name if detail else c_name
            norm_q = detail.quantity_normalized if detail else db_item.quantity
            std_u = detail.standard_unit if detail else db_item.unit
            u_p = detail.unit_price if detail else 0.0
            l_t = detail.line_total if detail else 0.0

            detailed_items.append(
                SavedBasketItemOut(
                    id=db_item.id,
                    commodity_id=db_item.commodity_id,
                    canonical_name=c_name,
                    bangla_name=b_name,
                    quantity=db_item.quantity,
                    unit=db_item.unit,
                    quantity_normalized=norm_q,
                    standard_unit=std_u,
                    unit_price=u_p,
                    line_total=l_t,
                )
            )

        return SavedBasketDetailOut(
            id=basket.id,
            name=basket.name,
            bangla_name=basket.bangla_name,
            description=basket.description,
            created_at=basket.created_at.isoformat() if basket.created_at else "",
            updated_at=basket.updated_at.isoformat() if basket.updated_at else "",
            calculation=calc_resp,
            items=detailed_items,
        )

    def delete_saved_basket(self, db: Session, basket_id: int) -> bool:
        """Delete a saved basket by ID."""
        basket = db.get(SavedBasket, basket_id)
        if not basket:
            return False
        db.delete(basket)
        db.commit()
        return True

    def calculate_basket_trend(
        self, db: Session, basket_id: int, days: int = 30
    ) -> Optional[BasketTrendResponse]:
        """
        Compute the chronological 30-day cost trajectory, volatility, and personal
        inflation rate for a saved consumer basket.
        """
        basket = db.get(SavedBasket, basket_id)
        if not basket or not basket.items:
            return None

        # Pre-normalize item quantities
        items_norm = []
        for item in basket.items:
            norm_q, std_u = self.normalize_item(item.quantity, item.unit)
            items_norm.append((item.commodity_id, norm_q, std_u))

        today = date.today()
        trend_points: list[BasketTrendPoint] = []
        retail_costs: list[float] = []

        for d in range(days - 1, -1, -1):
            obs_date = today - timedelta(days=d)
            daily_retail = 0.0
            daily_wholesale = 0.0
            daily_online = 0.0

            for comm_id, norm_q, _ in items_norm:
                ch = self._fetch_channel_prices(db, comm_id, obs_date)
                bench_p = ch.benchmark() or 0.0
                r_p = ch.retail or bench_p
                w_p = ch.wholesale or (bench_p * 0.85 if bench_p else 0.0)
                o_p = ch.online or (bench_p * 1.08 if bench_p else 0.0)

                daily_retail += r_p * norm_q
                daily_wholesale += w_p * norm_q
                daily_online += o_p * norm_q

            daily_retail = round(daily_retail, 2)
            daily_wholesale = round(daily_wholesale, 2)
            daily_online = round(daily_online, 2)

            retail_costs.append(daily_retail)
            trend_points.append(
                BasketTrendPoint(
                    date=obs_date.isoformat(),
                    retail_total=daily_retail,
                    wholesale_total=daily_wholesale,
                    online_total=daily_online,
                    is_anomaly_day=False,
                )
            )

        if not trend_points:
            return None

        # Statistical metrics
        avg_cost = round(sum(retail_costs) / len(retail_costs), 2)
        variance = (
            sum((c - avg_cost) ** 2 for c in retail_costs) / (len(retail_costs) - 1)
            if len(retail_costs) > 1
            else 0.0
        )
        std_dev = round(variance ** 0.5, 2)
        cv = round((std_dev / avg_cost) * 100.0, 2) if avg_cost > 0 else 0.0

        # Mark anomaly days (cost > mean + 1.5 * std_dev)
        anomaly_threshold = avg_cost + 1.5 * std_dev
        for pt in trend_points:
            if pt.retail_total >= anomaly_threshold and std_dev > 1.0:
                pt.is_anomaly_day = True

        current_cost = trend_points[-1].retail_total
        first_cost = trend_points[0].retail_total
        cost_7d_ago = trend_points[-7].retail_total if len(trend_points) >= 7 else first_cost

        inflation_30d = (
            round(((current_cost - first_cost) / first_cost) * 100.0, 2)
            if first_cost > 0
            else 0.0
        )
        inflation_7d = (
            round(((current_cost - cost_7d_ago) / cost_7d_ago) * 100.0, 2)
            if cost_7d_ago > 0
            else 0.0
        )

        cheapest_pt = min(trend_points, key=lambda x: x.retail_total)
        peak_pt = max(trend_points, key=lambda x: x.retail_total)

        b_name = basket.bangla_name or basket.name
        narrative = (
            f"পারিবারিক বাস্কেট '{b_name}'-এর ৩০ দিনের বিশ্লেষণ: "
            f"বর্তমান খুচরা মোট খরচ ৳{current_cost:.2f}, যা ৩০ দিন আগের (৳{first_cost:.2f}) তুলনায় "
            f"{inflation_30d:+.1f}% পরিবর্তিত হয়েছে (৭ দিনে {inflation_7d:+.1f}%)। "
            f"সর্বনিম্ন খরচ ছিল {cheapest_pt.date} তারিখে (৳{cheapest_pt.retail_total:.2f}) "
            f"এবং সর্বোচ্চ খরচ হয় {peak_pt.date} তারিখে (৳{peak_pt.retail_total:.2f})। "
            f"বাস্কেটটির ভোলাটিলিটি ইনডেক্স CV={cv:.1f}%, যা "
            f"{'উচ্চমূল্য অস্থিরতা নির্দেশ করে।' if cv >= 12.0 else 'তুলনামূলকভাবে স্থিতিশীল বাজার নির্দেশ করে।'}"
        )

        return BasketTrendResponse(
            basket_id=basket.id,
            basket_name=basket.name,
            bangla_name=basket.bangla_name,
            item_count=len(basket.items),
            current_cost=current_cost,
            baseline_30d_avg=avg_cost,
            inflation_30d_pct=inflation_30d,
            inflation_7d_pct=inflation_7d,
            cheapest_date=cheapest_pt.date,
            cheapest_cost=cheapest_pt.retail_total,
            peak_date=peak_pt.date,
            peak_cost=peak_pt.retail_total,
            volatility_cv=cv,
            trend_points=trend_points,
            academic_narrative=narrative,
        )


# Module-level singleton
basket_service = BasketOptimizationService()
