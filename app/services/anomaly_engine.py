"""
Statistical anomaly detection engine with explainable metrics and natural language justifications.
"""

import math
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.commodity import Commodity
from app.models.observation import PriceObservation
from app.schemas.anomaly import (
    MetricBreakdown,
    AnomalyDetailOut,
    AnomalyMonitorResponse,
)


class AnomalyEngine:
    """Calculates rolling statistical baselines, Z-scores, and rule-based explanations."""

    # Baseline window lengths in days
    WINDOW_7D = 7
    WINDOW_14D = 14
    WINDOW_30D = 30

    # Detection thresholds: Compound rule requires both statistical and percentage deviation
    Z_THRESHOLD_MODERATE = 1.5
    Z_THRESHOLD_SEVERE = 2.0
    Z_THRESHOLD_CRITICAL = 2.5

    DELTA_THRESHOLD_MODERATE = 10.0   # 10%
    DELTA_THRESHOLD_SEVERE = 20.0     # 20%
    DELTA_THRESHOLD_CRITICAL = 30.0   # 30%

    def calculate_sma(self, series: List[float]) -> Optional[float]:
        """Compute Simple Moving Average (SMA)."""
        if not series:
            return None
        return round(sum(series) / len(series), 2)

    def calculate_std_dev(self, series: List[float], sma: Optional[float] = None) -> Optional[float]:
        """Compute sample standard deviation."""
        if len(series) < 2:
            return 0.0
        mean = sma if sma is not None else (sum(series) / len(series))
        variance = sum((x - mean) ** 2 for x in series) / (len(series) - 1)
        return round(math.sqrt(variance), 4)

    def calculate_z_score(
        self, current_price: float, baseline_sma: float, std_dev: float
    ) -> float:
        """Compute standard score (Z-score)."""
        if std_dev <= 1e-6:
            return 0.0
        return round((current_price - baseline_sma) / std_dev, 2)

    def calculate_cv(self, std_dev: float, baseline_sma: float) -> float:
        """Calculate Volatility Coefficient of Variation (CV%)."""
        if baseline_sma <= 1e-6:
            return 0.0
        return round((std_dev / baseline_sma) * 100.0, 2)

    def evaluate_series(
        self,
        daily_prices: List[Tuple[date, float]],
        target_date: Optional[date] = None,
    ) -> Tuple[bool, str, Optional[str], MetricBreakdown]:
        """
        Evaluate time-series prices up to target_date and compute anomaly parameters.
        Returns: (is_anomaly, severity, direction, metrics)
        """
        if not daily_prices:
            return (
                False,
                "Normal",
                None,
                MetricBreakdown(current_price=0.0),
            )

        # Sort chronologically
        sorted_series = sorted(daily_prices, key=lambda x: x[0])
        eval_date = target_date or sorted_series[-1][0]

        # Partition into historical baseline and current observation
        history = [p for d, p in sorted_series if d < eval_date]
        target_entries = [p for d, p in sorted_series if d == eval_date]

        if not target_entries:
            # If target date has no observation, use the latest available
            current_price = sorted_series[-1][1]
            history = [p for d, p in sorted_series[:-1]]
        else:
            current_price = round(sum(target_entries) / len(target_entries), 2)

        # If history is sparse, fall back to whatever points exist
        if not history:
            return (
                False,
                "Normal",
                None,
                MetricBreakdown(current_price=current_price),
            )

        # Compute rolling window slices
        history_7d = history[-self.WINDOW_7D:] if len(history) >= self.WINDOW_7D else history
        history_14d = history[-self.WINDOW_14D:] if len(history) >= self.WINDOW_14D else history
        history_30d = history[-self.WINDOW_30D:] if len(history) >= self.WINDOW_30D else history

        sma_7d = self.calculate_sma(history_7d)
        sma_14d = self.calculate_sma(history_14d)
        sma_30d = self.calculate_sma(history_30d)

        # 14-day baseline is the primary operational benchmark
        baseline = sma_14d or sma_7d or current_price
        history_for_std = history_14d if len(history_14d) >= 2 else history
        std_dev_14d = self.calculate_std_dev(history_for_std, baseline)

        z_score = self.calculate_z_score(current_price, baseline, std_dev_14d)
        cv = self.calculate_cv(std_dev_14d, baseline)
        delta_pct = round(((current_price - baseline) / baseline) * 100.0, 2) if baseline > 0 else 0.0

        metrics = MetricBreakdown(
            current_price=current_price,
            baseline_sma_7d=sma_7d,
            baseline_sma_14d=sma_14d,
            baseline_sma_30d=sma_30d,
            std_dev_14d=std_dev_14d,
            z_score_14d=z_score,
            percentage_change_14d=delta_pct,
            volatility_cv=cv,
        )

        # Compound Anomaly Decision Rule
        abs_z = abs(z_score)
        abs_delta = abs(delta_pct)

        is_anomaly = (abs_z >= self.Z_THRESHOLD_MODERATE) and (abs_delta >= self.DELTA_THRESHOLD_MODERATE)

        if not is_anomaly:
            return False, "Normal", None, metrics

        direction = "Spike" if delta_pct > 0 else "Drop"

        if abs_z >= self.Z_THRESHOLD_CRITICAL and abs_delta >= self.DELTA_THRESHOLD_CRITICAL:
            severity = "Critical"
        elif abs_z >= self.Z_THRESHOLD_SEVERE and abs_delta >= self.DELTA_THRESHOLD_SEVERE:
            severity = "Severe"
        else:
            severity = "Moderate"

        return True, severity, direction, metrics

    def generate_explanation(
        self,
        commodity_name: str,
        unit: str,
        eval_date: date,
        is_anomaly: bool,
        severity: str,
        direction: Optional[str],
        metrics: MetricBreakdown,
    ) -> str:
        """Construct rule-based explainable academic justifications."""
        curr = f"{metrics.current_price:.2f} BDT/{unit}"
        base = f"{metrics.baseline_sma_14d:.2f} BDT/{unit}" if metrics.baseline_sma_14d else "N/A"
        z = f"{metrics.z_score_14d:+.2f}" if metrics.z_score_14d is not None else "0.0"
        delta = f"{metrics.percentage_change_14d:+.1f}%" if metrics.percentage_change_14d is not None else "0.0%"
        cv = f"{metrics.volatility_cv:.1f}%" if metrics.volatility_cv is not None else "0.0%"

        if not is_anomaly:
            return (
                f"{commodity_name} is trading within expected equilibrium thresholds at {curr} on {eval_date}. "
                f"The current price is {delta} relative to its 14-day baseline ({base}) with a stable Z-score "
                f"of {z} and moderate volatility (CV: {cv}). No significant market anomaly is present."
            )

        dir_word = "surge" if direction == "Spike" else "decline"
        dir_label = "price spike" if direction == "Spike" else "price collapse"

        return (
            f"Anomalous market pressure detected: {commodity_name} experienced a {severity.lower()} {dir_label} "
            f"reaching {curr} on {eval_date}. This reflects a {delta} {dir_word} over its 14-day baseline moving "
            f"average of {base}. The deviation is statistically significant at Z = {z} (σ = {metrics.std_dev_14d:.2f}), "
            f"surpassing the commodity's historical volatility envelope of {cv}."
        )

    def analyze_commodity(
        self,
        db: Session,
        commodity: Commodity,
        target_date: Optional[date] = None,
    ) -> AnomalyDetailOut:
        """Perform end-to-end anomaly detection and explanation for a commodity from database."""
        eval_date = target_date or date.today()
        # Query 45 days of daily average normalized prices for robust windowing
        start_date = eval_date - timedelta(days=45)

        stmt = (
            select(
                PriceObservation.observation_date,
                func.avg(PriceObservation.normalized_price).label("daily_avg"),
                func.avg(PriceObservation.confidence_score).label("avg_conf"),
            )
            .where(
                PriceObservation.commodity_id == commodity.id,
                PriceObservation.observation_date >= start_date,
                PriceObservation.observation_date <= eval_date,
            )
            .group_by(PriceObservation.observation_date)
            .order_by(PriceObservation.observation_date.asc())
        )
        rows = db.execute(stmt).all()

        daily_prices = [(r.observation_date, round(float(r.daily_avg), 2)) for r in rows]
        conf_scores = [float(r.avg_conf) for r in rows if r.avg_conf is not None]
        avg_confidence = round(sum(conf_scores) / len(conf_scores), 3) if conf_scores else 0.85

        is_anomaly, severity, direction, metrics = self.evaluate_series(
            daily_prices=daily_prices, target_date=eval_date
        )

        explanation = self.generate_explanation(
            commodity_name=commodity.canonical_name,
            unit=commodity.default_unit,
            eval_date=eval_date,
            is_anomaly=is_anomaly,
            severity=severity,
            direction=direction,
            metrics=metrics,
        )

        return AnomalyDetailOut(
            commodity_id=commodity.id,
            canonical_name=commodity.canonical_name,
            bangla_name=commodity.bangla_name,
            unit=commodity.default_unit,
            observation_date=eval_date,
            is_anomaly=is_anomaly,
            anomaly_severity=severity,
            anomaly_direction=direction,
            confidence_score=avg_confidence,
            metrics=metrics,
            explanation=explanation,
        )

    def detect_active_anomalies(
        self,
        db: Session,
        target_date: Optional[date] = None,
    ) -> AnomalyMonitorResponse:
        """Scan all commodities and compile active price alerts."""
        eval_date = target_date or date.today()
        commodities = list(db.scalars(select(Commodity).order_by(Commodity.id)).all())

        all_reports: List[AnomalyDetailOut] = []
        for comm in commodities:
            report = self.analyze_commodity(db=db, commodity=comm, target_date=eval_date)
            all_reports.append(report)

        active = [r for r in all_reports if r.is_anomaly]

        return AnomalyMonitorResponse(
            date=eval_date,
            total_monitored=len(all_reports),
            anomalies_detected=len(active),
            anomalies=active,
        )


anomaly_engine = AnomalyEngine()
