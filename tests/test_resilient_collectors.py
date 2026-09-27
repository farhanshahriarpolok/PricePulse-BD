"""
Tests for resilient live network collectors with graceful fallback to cached fixtures.
Verifies zero-downtime tolerance when upstream servers error or network fails.
"""

from unittest.mock import patch, MagicMock
import httpx
import pytest

from app.collectors.dam_live_collector import DAMLiveCollector
from app.collectors.chaldal_live_collector import ChaldalLiveCollector
from app.services.source_health import source_health_service


class TestDAMLiveCollectorResilience:
    """Test network failure resilience and fallback behavior for DAMLiveCollector."""

    def test_dam_collector_fallback_on_network_timeout(self):
        """When HTTP request times out, collector falls back to fixture without raising."""
        collector = DAMLiveCollector(live_url="http://invalid.dam.gov.bd/bulletin")

        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Connection timed out")):
            observations = collector.collect()

        assert len(observations) > 0
        # Check source health updated to DEGRADED
        telemetry = source_health_service.get_source_status("DAM_DAILY")
        assert telemetry is not None
        assert telemetry["status"] == "DEGRADED"
        assert telemetry["is_fallback"] is True
        assert "timed out" in telemetry["last_error"].lower() or "error" in telemetry["last_error"].lower()

    def test_dam_collector_fallback_on_500_status(self):
        """When server returns 500 Internal Server Error, collector falls back to fixture."""
        collector = DAMLiveCollector(live_url="http://invalid.dam.gov.bd/bulletin")

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("httpx.Client.get", return_value=mock_resp):
            observations = collector.collect()

        assert len(observations) > 0
        telemetry = source_health_service.get_source_status("DAM_DAILY")
        assert telemetry["status"] == "DEGRADED"
        assert telemetry["is_fallback"] is True

    def test_dam_collector_live_success(self):
        """When live request succeeds with valid HTML, source health is HEALTHY."""
        collector = DAMLiveCollector()
        sample_html = """
        <html>
            <body>
                <div class="bulletin-date" data-date="2026-09-28">28 September 2026</div>
                <div class="market-section" data-market="Kawran Bazar">
                    <table>
                        <tr class="item-row">
                            <td class="commodity-name">Onion (Local)</td>
                            <td class="unit-name">1 kg</td>
                            <td class="price-retail-avg">120.00</td>
                            <td class="price-wholesale-avg">110.00</td>
                        </tr>
                    </table>
                </div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_html

        with patch("httpx.Client.get", return_value=mock_resp):
            observations = collector.collect()

        assert len(observations) == 2  # retail and wholesale
        telemetry = source_health_service.get_source_status("DAM_DAILY")
        assert telemetry["status"] == "HEALTHY"
        assert telemetry["is_fallback"] is False


class TestChaldalLiveCollectorResilience:
    """Test network failure resilience and backoff fallback for ChaldalLiveCollector."""

    def test_chaldal_collector_fallback_on_connection_error(self):
        """When live catalog is unreachable, collector retries and falls back to fixture."""
        collector = ChaldalLiveCollector(api_url="https://invalid.chaldal.com/api", max_retries=2)

        with patch("httpx.Client.get", side_effect=httpx.ConnectError("Network unreachable")):
            observations = collector.collect()

        assert len(observations) > 0
        telemetry = source_health_service.get_source_status("CHALDAL_RETAIL")
        assert telemetry is not None
        assert telemetry["status"] == "DEGRADED"
        assert telemetry["is_fallback"] is True

    def test_chaldal_collector_fallback_on_429_rate_limit(self):
        """When API returns 429 Too Many Requests, collector falls back to fixture."""
        collector = ChaldalLiveCollector(max_retries=1)

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Too Many Requests"

        with patch("httpx.Client.get", return_value=mock_resp):
            observations = collector.collect()

        assert len(observations) > 0
        telemetry = source_health_service.get_source_status("CHALDAL_RETAIL")
        assert telemetry["status"] == "DEGRADED"
        assert telemetry["is_fallback"] is True

    def test_chaldal_collector_live_success(self):
        """When API returns valid JSON catalog, source health is HEALTHY."""
        collector = ChaldalLiveCollector()
        sample_json = {
            "catalog_date": "2026-09-28",
            "market_name": "Chaldal Live Hub",
            "items": [
                {
                    "name": "Local Onion 1 kg",
                    "price": 125.0,
                    "package_unit": "1 kg",
                    "in_stock": True,
                }
            ],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_json

        with patch("httpx.Client.get", return_value=mock_resp):
            observations = collector.collect()

        assert len(observations) == 1
        assert observations[0].raw_price == 125.0
        telemetry = source_health_service.get_source_status("CHALDAL_RETAIL")
        assert telemetry["status"] == "HEALTHY"
        assert telemetry["is_fallback"] is False
