"""
app/services/forecast_service.py
================================
Phase 3 Core Forecasting & Model Selection Engine.

Architectural Guarantees:
  Q1: Hybrid architecture (Baselines + ARIMA(1,1,0) + Rolling Backtesting + Model Selection).
  Q2: Channel-separated national aggregation (Wholesale, Retail, Online, and Combined).
  Q3: Verified populated market series with explicit channel labels; unpopulated markets rejected.
  Q4: Volatility-aware direction threshold (Base ±3.0%, modulated by historical CV).
  Data Eligibility: Strict exclusion of PANDAMART_MODELED and sparse commodities.
  Zero Future Leakage: Strict chronological rolling-origin walk-forward validation.
"""

import math
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.models.commodity import Commodity
from app.models.location import Market, District
from app.models.observation import PriceObservation
from app.models.source import Source
from app.services.anomaly_engine import AnomalyEngine
from app.services.normalizer import CommodityNormalizer, commodity_normalizer
from app.schemas.forecast import (
    DailyForecastPoint,
    ModelBacktestMetric,
    DataEligibilityDetail,
    SeriesScopeMetadata,
    DirectionSignalDetail,
    ForecastSummaryDetail,
    CommodityForecastResponse,
)


class ForecastService:
    """Production time-series forecasting and model evaluation engine."""

    HORIZON_DAYS = 7
    MIN_TRAIN_DAYS = 14
    MIN_TOTAL_DAYS = 14

    def __init__(self, normalizer: Optional[CommodityNormalizer] = None):
        self.normalizer = normalizer or commodity_normalizer
        self.anomaly_engine = AnomalyEngine()

    def resolve_commodity(self, db: Session, commodity_identifier: str) -> Optional[Commodity]:
        """Resolve commodity ID or localized name to Commodity instance."""
        raw_str = str(commodity_identifier).strip()
        if raw_str.isdigit():
            return db.get(Commodity, int(raw_str))

        sanitized = raw_str.replace("_", " ").replace("-", " ")
        match = self.normalizer.resolve_commodity(sanitized)
        if match:
            stmt = select(Commodity).where(Commodity.canonical_name == match.canonical_name)
            comm = db.scalars(stmt).first()
            if comm:
                return comm

        stmt = select(Commodity).where(
            (Commodity.canonical_name.ilike(f"%{sanitized}%"))
            | (Commodity.bangla_name.ilike(f"%{sanitized}%"))
        )
        return db.scalars(stmt).first()

    # ── 1. Data Eligibility & Series Extraction ───────────────────────────────

    def get_empirical_series(
        self,
        db: Session,
        commodity_id: int,
        channel: str = "wholesale",
        market_id: Optional[int] = None,
    ) -> Tuple[List[Tuple[date, float]], DataEligibilityDetail, SeriesScopeMetadata]:
        """
        Build an empirical chronological date -> price series.
        STRICT RULE: Excludes PANDAMART_MODELED and any non-empirical sources.
        """
        # Resolve scope metadata
        market_name = None
        district_name = None
        scope = "national"

        if market_id:
            m = db.get(Market, market_id)
            if m:
                scope = "market"
                market_name = m.name
                if m.district:
                    district_name = m.district.name
            else:
                scope = "market"

        scope_meta = SeriesScopeMetadata(
            scope=scope,
            channel=channel.lower(),
            market_id=market_id,
            market_name=market_name,
            district_name=district_name,
        )

        # 1. Count excluded modeled observations (PANDAMART_MODELED)
        modeled_stmt = (
            select(func.count(PriceObservation.id))
            .join(Source, PriceObservation.source_id == Source.id)
            .where(
                PriceObservation.commodity_id == commodity_id,
                Source.code == "PANDAMART_MODELED",
            )
        )
        if market_id:
            modeled_stmt = modeled_stmt.where(PriceObservation.market_id == market_id)
        modeled_excluded = db.scalar(modeled_stmt) or 0

        # 2. Build base empirical query (Excluding PANDAMART_MODELED)
        query = (
            select(
                PriceObservation.observation_date,
                func.avg(PriceObservation.normalized_price).label("avg_price"),
                func.count(PriceObservation.id).label("obs_count"),
            )
            .join(Source, PriceObservation.source_id == Source.id)
            .where(
                PriceObservation.commodity_id == commodity_id,
                Source.code != "PANDAMART_MODELED",
            )
        )

        # Apply market filter if requested
        if market_id:
            query = query.where(PriceObservation.market_id == market_id)
        else:
            # National channel separation
            ch = channel.lower()
            if ch == "wholesale":
                query = query.where(PriceObservation.price_type.like("%wholesale%"))
            elif ch == "retail":
                query = query.where(
                    (PriceObservation.price_type.like("%retail%"))
                    & (Source.code != "CHALDAL_RETAIL")
                )
            elif ch == "online":
                query = query.where(
                    (Source.code == "CHALDAL_RETAIL")
                    | (PriceObservation.market_id.in_(
                        select(Market.id).where(Market.market_type == "online")
                    ))
                )
            # 'all' applies no channel restriction

        query = query.group_by(PriceObservation.observation_date).order_by(
            PriceObservation.observation_date.asc()
        )

        rows = db.execute(query).all()

        if not rows:
            eligibility = DataEligibilityDetail(
                eligible=False,
                observation_count=0,
                distinct_dates_count=0,
                date_start=None,
                date_end=None,
                longest_daily_streak=0,
                modeled_observations_excluded=modeled_excluded,
                reason="No empirical observations available for requested scope/channel.",
            )
            return [], eligibility, scope_meta

        series: List[Tuple[date, float]] = [
            (row.observation_date, round(float(row.avg_price), 2)) for row in rows
        ]
        total_obs = sum(int(row.obs_count) for row in rows)
        dates = [d for d, _ in series]

        # Calculate longest consecutive daily streak
        longest_streak = 0
        curr_streak = 0
        prev_d = None
        for d in dates:
            if prev_d is None or d == prev_d + timedelta(days=1):
                curr_streak += 1
            else:
                curr_streak = 1
            if curr_streak > longest_streak:
                longest_streak = curr_streak
            prev_d = d

        is_eligible = (
            len(series) >= self.MIN_TOTAL_DAYS
            and longest_streak >= 7
        )

        reason = None
        if not is_eligible:
            if len(series) < self.MIN_TOTAL_DAYS:
                reason = f"Insufficient history: {len(series)} dates found, minimum {self.MIN_TOTAL_DAYS} required."
            elif longest_streak < 7:
                reason = f"Sparsity gap: longest continuous daily streak is {longest_streak} days, minimum 7 required."

        eligibility = DataEligibilityDetail(
            eligible=is_eligible,
            observation_count=total_obs,
            distinct_dates_count=len(series),
            date_start=dates[0],
            date_end=dates[-1],
            longest_daily_streak=longest_streak,
            modeled_observations_excluded=modeled_excluded,
            reason=reason,
        )

        return series, eligibility, scope_meta

    # ── 2. Candidate Models Implementation ────────────────────────────────────

    @staticmethod
    def forecast_naive(train_prices: List[float], steps: int = 7) -> List[float]:
        """Naive Persistence: forecast = last observed value."""
        last_val = train_prices[-1]
        return [last_val] * steps

    @staticmethod
    def forecast_sma(train_prices: List[float], window: int, steps: int = 7) -> List[float]:
        """Moving Average: forecast = mean of the last `window` observations."""
        slice_vals = train_prices[-window:] if len(train_prices) >= window else train_prices
        mean_val = round(sum(slice_vals) / len(slice_vals), 2)
        return [mean_val] * steps

    @staticmethod
    def forecast_arima_1_1_0(train_prices: List[float], steps: int = 7) -> Tuple[List[float], bool, Optional[str]]:
        """
        Fit non-seasonal ARIMA(1,1,0).
        First attempts statsmodels; gracefully falls back to exact analytical OLS AR(1) on differenced series.
        Returns: (forecasts, success_flag, error_or_fallback_reason)
        """
        if len(train_prices) < 5:
            return [train_prices[-1]] * steps, False, "Series too short for ARIMA(1,1,0)"

        # Try statsmodels ARIMA
        try:
            import warnings
            from statsmodels.tsa.arima.model import ARIMA
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ARIMA(train_prices, order=(1, 1, 0), enforce_stationarity=False)
                res = model.fit()
                fc = res.forecast(steps=steps)
            fc_list = [round(float(v), 2) for v in fc]
            return fc_list, True, None
        except Exception as e:
            # Fall back to exact analytical OLS AR(1) on first differences:
            # Delta y_t = c + phi * Delta y_{t-1}
            diffs = [train_prices[i] - train_prices[i - 1] for i in range(1, len(train_prices))]
            if len(diffs) < 3:
                return [train_prices[-1]] * steps, False, f"Statsmodels failed ({e}); diffs too short"

            # OLS for AR(1) on diffs: y_diff = z
            z_y = diffs[1:]
            z_x = diffs[:-1]
            n_d = len(z_y)
            mean_y = sum(z_y) / n_d
            mean_x = sum(z_x) / n_d

            var_x = sum((x - mean_x) ** 2 for x in z_x)
            if var_x < 1e-7:
                # Zero variance in diffs: prices are linear or constant
                drift = diffs[-1]
                fc = [round(train_prices[-1] + (h + 1) * drift, 2) for h in range(steps)]
                return fc, True, "Analytical OLS AR(1) zero-variance fallback"

            cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(z_x, z_y))
            phi = cov_xy / var_x
            # Stationarity clip
            phi = max(min(phi, 0.92), -0.92)
            c = mean_y - phi * mean_x

            # Step-by-step diff forecast
            fc = []
            last_diff = diffs[-1]
            last_price = train_prices[-1]

            curr_diff = last_diff
            curr_price = last_price
            for _ in range(steps):
                curr_diff = c + phi * curr_diff
                curr_price += curr_diff
                fc.append(round(curr_price, 2))

            return fc, True, f"Analytical OLS AR(1) (Statsmodels fallback: {e})"

    # ── 3. Rolling Walk-Forward Backtesting Engine ─────────────────────────────

    def run_rolling_backtest(
        self,
        full_prices: List[float],
        min_train: int = 14,
        horizon: int = 7,
    ) -> Tuple[List[ModelBacktestMetric], str, Optional[str]]:
        """
        Evaluate candidate models using chronological rolling-origin walk-forward validation.
        STRICT: Zero future data leakage. Training slice is strictly [0..t-1], actual is [t..t+horizon-1].
        """
        n = len(full_prices)
        if n < min_train + horizon:
            return [], "NAIVE", f"Insufficient points for backtesting (have {n}, need {min_train + horizon})"

        candidate_names = ["NAIVE", "SMA_7", "SMA_14", "ARIMA_1_1_0"]
        errors: Dict[str, List[float]] = {name: [] for name in candidate_names}
        sq_errors: Dict[str, List[float]] = {name: [] for name in candidate_names}
        pct_errors: Dict[str, List[float]] = {name: [] for name in candidate_names}
        arima_fallbacks = []

        windows_count = 0
        for cutoff in range(min_train, n - horizon + 1):
            windows_count += 1
            train_slice = full_prices[:cutoff]
            actual_slice = full_prices[cutoff : cutoff + horizon]

            # 1. NAIVE
            pred_naive = self.forecast_naive(train_slice, steps=horizon)
            # 2. SMA-7
            pred_sma7 = self.forecast_sma(train_slice, window=7, steps=horizon)
            # 3. SMA-14
            pred_sma14 = self.forecast_sma(train_slice, window=14, steps=horizon)
            # 4. ARIMA(1,1,0)
            pred_arima, arima_ok, arima_reason = self.forecast_arima_1_1_0(train_slice, steps=horizon)
            if not arima_ok:
                arima_fallbacks.append(arima_reason)

            preds = {
                "NAIVE": pred_naive,
                "SMA_7": pred_sma7,
                "SMA_14": pred_sma14,
                "ARIMA_1_1_0": pred_arima,
            }

            for name, pred in preds.items():
                for actual, p in zip(actual_slice, pred):
                    err = abs(actual - p)
                    sq_err = (actual - p) ** 2
                    errors[name].append(err)
                    sq_errors[name].append(sq_err)
                    if actual > 1e-4:
                        pct_errors[name].append((err / actual) * 100.0)

        metrics: List[ModelBacktestMetric] = []
        best_model = "NAIVE"
        best_mae = float("inf")

        for name in candidate_names:
            mae = round(sum(errors[name]) / len(errors[name]), 2) if errors[name] else 999.0
            rmse = round(math.sqrt(sum(sq_errors[name]) / len(sq_errors[name])), 2) if sq_errors[name] else 999.0
            mape = round(sum(pct_errors[name]) / len(pct_errors[name]), 2) if pct_errors[name] else None

            metrics.append(
                ModelBacktestMetric(
                    model_name=name,
                    is_selected=False,
                    windows_evaluated=windows_count,
                    mae_bdt=mae,
                    rmse_bdt=rmse,
                    mape_pct=mape,
                    fit_successful=True,
                )
            )

            # Preference: Lower MAE wins. In tie, order of candidate_names breaks tie.
            if mae < best_mae:
                best_mae = mae
                best_model = name

        for m in metrics:
            if m.model_name == best_model:
                m.is_selected = True

        fallback_msg = None
        if best_model != "ARIMA_1_1_0":
            fallback_msg = f"Model '{best_model}' outperformed ARIMA(1,1,0) on rolling backtest MAE (BDT {best_mae:.2f})"
        elif arima_fallbacks:
            fallback_msg = f"ARIMA selected with fallbacks: {arima_fallbacks[0]}"

        return metrics, best_model, fallback_msg

    # ── 4. Main Forecasting & Synthesis Pipeline ───────────────────────────────

    def generate_commodity_forecast(
        self,
        db: Session,
        commodity_identifier: str,
        channel: str = "wholesale",
        market_id: Optional[int] = None,
    ) -> CommodityForecastResponse:
        """
        Generate complete forecast, model selection, intervals, and direction signal.
        """
        comm = self.resolve_commodity(db, commodity_identifier)
        if not comm:
            # Non-existent commodity
            scope_meta = SeriesScopeMetadata(
                scope="market" if market_id else "national",
                channel=channel.lower(),
                market_id=market_id,
            )
            eligibility = DataEligibilityDetail(
                eligible=False,
                observation_count=0,
                distinct_dates_count=0,
                reason=f"Commodity '{commodity_identifier}' does not exist.",
            )
            return CommodityForecastResponse(
                commodity_id=0,
                canonical_name=str(commodity_identifier),
                bangla_name=None,
                calculation_unit="kg",
                status="UNAVAILABLE",
                series_metadata=scope_meta,
                data_eligibility=eligibility,
                direction_signal=DirectionSignalDetail(
                    direction="UNAVAILABLE",
                    recent_change_pct=0.0,
                    direction_summary="Commodity not found in taxonomy.",
                ),
            )

        # 1. Fetch Empirical Series
        series, eligibility, scope_meta = self.get_empirical_series(
            db=db,
            commodity_id=comm.id,
            channel=channel,
            market_id=market_id,
        )

        if not eligibility.eligible or len(series) < self.MIN_TOTAL_DAYS:
            # Insufficient Data failure state
            return CommodityForecastResponse(
                commodity_id=comm.id,
                canonical_name=comm.canonical_name,
                bangla_name=comm.bangla_name,
                calculation_unit=comm.default_unit,
                status="INSUFFICIENT_DATA",
                series_metadata=scope_meta,
                data_eligibility=eligibility,
                direction_signal=DirectionSignalDetail(
                    direction="UNAVAILABLE",
                    recent_change_pct=0.0,
                    direction_summary=eligibility.reason or "Insufficient historical observations for forecasting.",
                ),
            )

        prices = [p for _, p in series]
        dates = [d for d, _ in series]
        current_price = prices[-1]
        last_date = dates[-1]

        # 2. Run Rolling Backtest & Model Selection
        backtest_metrics, selected_model, fallback_msg = self.run_rolling_backtest(
            prices, min_train=self.MIN_TRAIN_DAYS, horizon=self.HORIZON_DAYS
        )

        # 3. Fit Winning Model on full data and forecast day 1..7
        if selected_model == "NAIVE":
            point_forecasts = self.forecast_naive(prices, steps=self.HORIZON_DAYS)
        elif selected_model == "SMA_7":
            point_forecasts = self.forecast_sma(prices, window=7, steps=self.HORIZON_DAYS)
        elif selected_model == "SMA_14":
            point_forecasts = self.forecast_sma(prices, window=14, steps=self.HORIZON_DAYS)
        else:
            point_forecasts, _, arima_err = self.forecast_arima_1_1_0(prices, steps=self.HORIZON_DAYS)
            if arima_err and not fallback_msg:
                fallback_msg = arima_err

        # 4. Uncertainty Intervals: Based on winning model's out-of-sample RMSE
        selected_metric = next((m for m in backtest_metrics if m.model_name == selected_model), None)
        base_rmse = selected_metric.rmse_bdt if selected_metric else 2.50
        base_rmse = max(base_rmse, 1.0)  # non-zero floor

        daily_points: List[DailyForecastPoint] = []
        for h in range(1, self.HORIZON_DAYS + 1):
            pf = point_forecasts[h - 1]
            # Uncertainty scales with sqrt of horizon
            step_sigma = base_rmse * math.sqrt(1.0 + 0.10 * (h - 1))
            lb = max(0.0, round(pf - 1.96 * step_sigma, 2))
            ub = round(pf + 1.96 * step_sigma, 2)
            cal_date = last_date + timedelta(days=h)
            daily_points.append(
                DailyForecastPoint(
                    day_offset=h,
                    target_date=cal_date,
                    predicted_price_bdt=pf,
                    lower_bound_bdt=lb,
                    upper_bound_bdt=ub,
                )
            )

        day7_point = daily_points[-1]

        # 5. Volatility-Aware Direction Signal (Q4)
        pct_change_7d = round(((day7_point.predicted_price_bdt - current_price) / current_price) * 100.0, 2) if current_price > 0 else 0.0

        # Calculate 14-day historical CV
        slice_14d = prices[-14:] if len(prices) >= 14 else prices
        mean_14d = sum(slice_14d) / len(slice_14d)
        std_14d = self.anomaly_engine.calculate_std_dev(slice_14d, mean_14d) or 0.0
        cv_14d = round((std_14d / mean_14d) * 100.0, 1) if mean_14d > 0 else 0.0

        # Dynamic deadband: Base ±3.0%, widens up to ±7.0% for high volatility regimes (CV > 8%)
        base_deadband = 3.0
        effective_deadband = base_deadband
        if cv_14d > 8.0:
            volatility_expansion = min(4.0, (cv_14d - 8.0) * 0.4)
            effective_deadband = round(base_deadband + volatility_expansion, 1)

        if pct_change_7d > effective_deadband:
            direction = "UP"
            dir_summary = (
                f"দাম ঊর্ধ্বমুখী হতে পারে: আগামী ৭ দিনে প্রায় {pct_change_7d:+.1f}% বৃদ্ধির সম্ভাবনা "
                f"(বাজারের অস্থিরতা CV: {cv_14d}%)।"
            )
        elif pct_change_7d < -effective_deadband:
            direction = "DOWN"
            dir_summary = (
                f"দাম নিম্নমুখী হতে পারে: আগামী ৭ দিনে প্রায় {pct_change_7d:+.1f}% কমার সম্ভাবনা "
                f"(বাজারের অস্থিরতা CV: {cv_14d}%)।"
            )
        else:
            direction = "STABLE"
            dir_summary = (
                f"দাম স্থিতিশীল থাকার সম্ভাবনা: ৭ দিনের পূর্বাভাস {pct_change_7d:+.1f}% "
                f"যা কার্যকর থ্রেশহোল্ড ±{effective_deadband:.1f}% এর মধ্যে।"
            )

        direction_signal = DirectionSignalDetail(
            direction=direction,
            recent_change_pct=pct_change_7d,
            base_threshold_pct=base_deadband,
            historical_cv_pct=cv_14d,
            effective_threshold_pct=effective_deadband,
            direction_summary=dir_summary,
        )

        forecast_detail = ForecastSummaryDetail(
            horizon_days=self.HORIZON_DAYS,
            selected_model=selected_model,
            candidate_models=[m.model_name for m in backtest_metrics],
            selection_metric="MAE",
            fallback_reason=fallback_msg,
            interval_method="Parametric 95% interval derived from rolling walk-forward RMSE",
            current_observed_price_bdt=current_price,
            forecast_day7_bdt=day7_point.predicted_price_bdt,
            forecast_day7_lower_bdt=day7_point.lower_bound_bdt,
            forecast_day7_upper_bdt=day7_point.upper_bound_bdt,
            daily_schedule=daily_points,
        )

        return CommodityForecastResponse(
            commodity_id=comm.id,
            canonical_name=comm.canonical_name,
            bangla_name=comm.bangla_name,
            calculation_unit=comm.default_unit,
            status="FORECAST",
            series_metadata=scope_meta,
            data_eligibility=eligibility,
            direction_signal=direction_signal,
            forecast_detail=forecast_detail,
            backtest_metrics=backtest_metrics,
        )


forecast_service = ForecastService()
