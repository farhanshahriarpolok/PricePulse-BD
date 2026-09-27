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

    def __init__(self, weights: Optional[dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Confidence weights must sum to 1.0, got {total}")

    def compute(
        self,
        source_reliability: float,
        alias_weight: float,
        observation_date: date,
        completeness_score: float = 1.0,
        reference_date: Optional[date] = None,
    ) -> float:
        """
        Calculate composite confidence score C in [0.0, 1.0].
        
        Args:
            source_reliability: Publisher credibility score [0.0, 1.0].
            alias_weight: Precision of taxonomy/alias resolution [0.0, 1.0].
            observation_date: Calendar date of the bulletin price.
            completeness_score: Presence of ranges, units, and spatial tags [0.0, 1.0].
            reference_date: Anchor date for freshness decay calculation.
        """
        s_src = max(0.0, min(1.0, float(source_reliability)))
        s_alias = max(0.0, min(1.0, float(alias_weight)))
        s_cmpl = max(0.0, min(1.0, float(completeness_score)))

        ref = reference_date or observation_date
        days_diff = max(0, (ref - observation_date).days)
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


confidence_scorer = ConfidenceScorer()
