"""
Services package: normalization, confidence scoring, analytics, anomalies, and spatial intelligence.
"""

from app.services.confidence import ConfidenceScorer, confidence_scorer
from app.services.normalizer import (
    CommodityNormalizer,
    NormalizedCommodity,
    commodity_normalizer,
)
from app.services.ingestion import IngestionPipeline, IngestionReport
from app.services.analytics import AnalyticsService, analytics_service
from app.services.realtime_service import RealtimePriceService
from app.services.anomaly_engine import AnomalyEngine, anomaly_engine
from app.services.spatial_service import SpatialService, spatial_service
from app.services.source_health import SourceHealthService, source_health_service
from app.services.scheduler import BackgroundSyncScheduler, sync_scheduler

__all__ = [
    "ConfidenceScorer",
    "confidence_scorer",
    "CommodityNormalizer",
    "NormalizedCommodity",
    "commodity_normalizer",
    "IngestionPipeline",
    "IngestionReport",
    "AnalyticsService",
    "analytics_service",
    "RealtimePriceService",
    "AnomalyEngine",
    "anomaly_engine",
    "SpatialService",
    "spatial_service",
    "SourceHealthService",
    "source_health_service",
    "BackgroundSyncScheduler",
    "sync_scheduler",
]
