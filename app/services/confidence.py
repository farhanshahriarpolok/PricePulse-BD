"""
Weighted linear confidence scoring engine for normalized price observations.
"""

from datetime import date
from typing import Optional


class ConfidenceScorer:
    """Computes multi-factor composite confidence metrics for market observations."""

    # Default weights sum to 1.0
    DEFAULT_WEIGHTS = {
        "source": 0.40,
        "alias": 0.30,
        "freshness": 0.15,
        "completeness": 0.15,
    }

    # Standard source reliability scalars by tier and code
    SOURCE_TIERS = {
        1: 0.90,  # Statutory government bulletin (DAM)
        2: 0.88,  # State trading corporation (TCB)
        3: 0.85,  # Verified digital retail grocery (Chaldal, Shwapno)
        4: 0.60,  # Unverified crowdsourced field spot report
    }

    SOURCE_CODE_RELIABILITY = {
        "dam_bulletin": 0.90,
        "tcb_bulletin": 0.88,
        "chaldal_retail": 0.85,
        "field_report": 0.60,
        "manual_field": 0.60,
        "DAM_DAILY": 0.95,
        "TCB_DAILY": 0.90,
        "CHALDAL_RETAIL": 0.88,
        "PRESS_REPORT": 0.70,
    }

    def __init__(self, weights: Optional[dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Confidence weights must sum to 1.0, got {total}")

    def compute(
        self,
        source_reliability: float = 0.80,
        alias_weight: float = 1.0,
        observation_date: Optional[date] = None,
        completeness_score: float = 1.0,
        reference_date: Optional[date] = None,
        source_tier: Optional[int] = None,
        source_code: Optional[str] = None,
    ) -> float:
        """
        Calculate composite confidence score C in [0.0, 1.0].
        
        Args:
            source_reliability: Publisher credibility score [0.0, 1.0].
            alias_weight: Precision of taxonomy/alias resolution [0.0, 1.0].
            observation_date: Calendar date of the bulletin price.
            completeness_score: Presence of ranges, units, and spatial tags [0.0, 1.0].
            reference_date: Anchor date for freshness decay calculation.
            source_tier: Optional tier classification (1=Gov, 2=State, 3=Retail, 4=Field).
            source_code: Optional source identifier code.
        """
        obs_date = observation_date or date.today()

        # Resolve source reliability scalar with tier/code overrides
        s_rel = float(source_reliability)
        if source_tier is not None and source_tier in self.SOURCE_TIERS:
            s_rel = self.SOURCE_TIERS[source_tier]
        elif source_code is not None and source_code in self.SOURCE_CODE_RELIABILITY:
            s_rel = self.SOURCE_CODE_RELIABILITY[source_code]

        s_src = max(0.0, min(1.0, s_rel))
        s_alias = max(0.0, min(1.0, float(alias_weight)))
        s_cmpl = max(0.0, min(1.0, float(completeness_score)))

        ref = reference_date or obs_date
        days_diff = max(0, (ref - obs_date).days)
        # Freshness decays by 0.1 per day of age, floor at 0.2
        s_fresh = max(0.2, 1.0 - (0.1 * days_diff))

        w = self.weights
        score = (
            w["source"] * s_src
            + w["alias"] * s_alias
            + w["freshness"] * s_fresh
            + w["completeness"] * s_cmpl
        )
        return round(max(0.0, min(1.0, score)), 4)

    def compute_field_report_confidence(
        self,
        observation_date: Optional[date] = None,
        reference_date: Optional[date] = None,
        has_note: bool = False,
    ) -> float:
        """
        Calibrated confidence calculation for manual field spot reports.
        Applies Tier 4 unverified baseline (0.60) to prevent outlier poisoning.
        """
        completeness = 1.0 if has_note else 0.85
        return self.compute(
            source_reliability=0.60,
            alias_weight=1.0,
            observation_date=observation_date or date.today(),
            completeness_score=completeness,
            reference_date=reference_date,
            source_tier=4,
        )


confidence_scorer = ConfidenceScorer()

