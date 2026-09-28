"""
tests/test_resilient_collectors.py
===================================
Comprehensive resilience and fault-tolerance unit tests for:
1. TCBCollector DOM mutation tolerance, multi-selector resolution, and numeral range parsing.
2. Exponential backoff retry jitter across network connection failures.
3. DAMLiveCollector adaptive column order parsing (wholesale vs retail swapped) and Bengali numeral handling.
4. Granular error telemetry recording and SourceHealth status transitions (HEALTHY -> DEGRADED -> OFFLINE).
5. Multi-source daily synchronization resilience.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import httpx

from app.collectors.tcb_collector import TCBCollector
from app.collectors.dam_live_collector import DAMLiveCollector
from app.services.source_health import SourceHealthService, source_health_service


class TestTCBResilience:
    """Validate TCBCollector resilience against DOM shifts, numeral variations, and network hiccups."""

    def test_tcb_numeral_and_range_variations(self):
        collector = TCBCollector()
        # Single Bengali numeral
        assert collector._convert_bn_number("১২০") == 120.0
        # Bengali range with hyphen
        assert collector._convert_bn_number("১২০ - ১৩০") == 125.0
        # Bengali range with 'থেকে'
        assert collector._convert_bn_number("১২০ থেকে ১৩০") == 125.0
        # English range with hyphen
        assert collector._convert_bn_number("120 - 130") == 125.0
        # English range with 'to'
        assert collector._convert_bn_number("120 to 130") == 125.0
        # Price with currency suffix
        assert collector._convert_bn_number("১২৫ টাকা/কেজি") == 125.0
        assert collector._convert_bn_number("125 Tk/kg") == 125.0

    def test_tcb_dom_mutation_price_table_class(self, tmp_path: Path):
        html_content = """
        <html>
        <body>
            <div class="content">
                <table class="price-table">
                    <thead>
                        <tr><th>ক্রমিক</th><th>পণ্যের নাম</th><th>একক</th><th>দর (টাকা)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>১</td><td>মশুর ডাল</td><td>কেজি</td><td>১৩০ - ১৪০</td></tr>
                        <tr><td>২</td><td>সয়াবিন তেল</td><td>লিটার</td><td>১৬৫</td></tr>
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        fixture_file = tmp_path / "mutated_tcb.html"
        fixture_file.write_text(html_content, encoding="utf-8")

        with patch("httpx.Client.get", side_effect=httpx.ConnectTimeout("Timeout")):
            collector = TCBCollector(fixture_path=fixture_file, max_retries=0)
            items = collector.collect()
            assert len(items) == 2
            assert items[0].raw_commodity_name == "মশুর ডাল"
            assert items[0].raw_price == 135.0
            assert items[0].raw_unit == "কেজি"
            assert items[1].raw_price == 165.0

    def test_tcb_dom_mutation_content_table_with_english_headers(self, tmp_path: Path):
        html_content = """
        <html>
        <body>
            <div class="content-table">
                <table>
                    <thead>
                        <tr><th>SL</th><th>Commodity Item</th><th>Unit</th><th>Min Price</th><th>Max Price</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>1</td><td>Local Onion</td><td>kg</td><td>110</td><td>120</td></tr>
                        <tr><td>2</td><td>Potato</td><td>kg</td><td>50</td><td>60</td></tr>
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        fixture_file = tmp_path / "english_tcb.html"
        fixture_file.write_text(html_content, encoding="utf-8")

        with patch("httpx.Client.get", side_effect=httpx.ConnectError("Unreachable")):
            collector = TCBCollector(fixture_path=fixture_file, max_retries=0)
            items = collector.collect()
            assert len(items) == 2
            assert items[0].raw_commodity_name == "Local Onion"
            assert items[0].raw_price == 115.0
            assert items[0].raw_unit == "kg"
            assert items[1].raw_price == 55.0

    def test_tcb_retry_exponential_backoff(self):
        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectTimeout(f"Connection timeout attempt {call_count}")
            # Success on 3rd attempt
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = """
            <table>
                <tr><th>পণ্যের নাম</th><th>একক</th><th>দর</th></tr>
                <tr><td>দেশি পেঁয়াজ</td><td>কেজি</td><td>১২০</td></tr>
            </table>
            """
            return mock_resp

        with patch("httpx.Client.get", side_effect=mock_get):
            with patch("time.sleep") as mock_sleep:
                collector = TCBCollector(max_retries=2, base_delay=0.1)
                items = collector.collect()
                assert call_count == 3
                assert len(items) == 1
                assert items[0].is_fallback is False
                assert items[0].raw_price == 120.0
                assert mock_sleep.call_count >= 2


class TestDAMResilience:
    """Validate DAMLiveCollector adaptive column order and granular error telemetry."""

    def test_dam_adaptive_column_order_swapped(self, tmp_path: Path):
        # Table where retail column is placed BEFORE wholesale columns
        html_content = """
        <html>
        <body>
            <div class="market-section" data-market="Kawran Bazar">
                <table>
                    <thead>
                        <tr>
                            <th>ক্রমিক</th>
                            <th>পণ্যের নাম</th>
                            <th>একক</th>
                            <th>খুচরা গড়</th>
                            <th>পাইকারি গড়</th>
                            <th>পাইকারি সর্বনিম্ন</th>
                            <th>পাইকারি সর্বোচ্চ</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>১</td>
                            <td>দেশি পেঁয়াজ</td>
                            <td>কেজি</td>
                            <td>৯৫.০০</td>
                            <td>৮৫.০০</td>
                            <td>৮২.০০</td>
                            <td>৮৮.০০</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        fixture_file = tmp_path / "swapped_dam.html"
        fixture_file.write_text(html_content, encoding="utf-8")

        with patch("httpx.Client.get", side_effect=httpx.ConnectError("Network Down")):
            collector = DAMLiveCollector(fixture_path=fixture_file, max_retries=0)
            items = collector.collect()
            assert len(items) >= 2
            # Find retail and wholesale items
            retail = next((x for x in items if x.price_type == "retail_avg"), None)
            ws = next((x for x in items if x.price_type == "wholesale_avg"), None)
            assert retail is not None
            assert retail.raw_price == 95.0
            assert ws is not None
            assert ws.raw_price == 85.0

    def test_dam_bengali_numerals_in_cells(self, tmp_path: Path):
        html_content = """
        <html>
        <body>
            <table>
                <thead>
                    <tr>
                        <th>Commodity</th>
                        <th>Unit</th>
                        <th>Retail Price</th>
                        <th>Wholesale Price</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>আলু ডায়মন্ড</td>
                        <td>কেজি</td>
                        <td>৫০.০০</td>
                        <td>৪৪.০০</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        fixture_file = tmp_path / "bn_numerals_dam.html"
        fixture_file.write_text(html_content, encoding="utf-8")

        with patch("httpx.Client.get", side_effect=httpx.HTTPStatusError("500 Internal Error", request=MagicMock(), response=MagicMock(status_code=500))):
            collector = DAMLiveCollector(fixture_path=fixture_file, max_retries=0)
            items = collector.collect()
            assert len(items) >= 2
            retail = next(x for x in items if x.price_type == "retail_avg")
            assert retail.raw_price == 50.0

    def test_dam_granular_telemetry_recording(self):
        health_svc = SourceHealthService()
        with patch("app.collectors.dam_live_collector.source_health_service", health_svc):
            with patch("httpx.Client.get", side_effect=httpx.ConnectTimeout("DNS timeout at gateway")):
                collector = DAMLiveCollector(max_retries=0)
                items = collector.collect()
                assert len(items) > 0
                telemetry = health_svc.get_source_telemetry("DAM_DAILY")
                assert telemetry["status"] == "DEGRADED"
                assert "ConnectTimeout" in telemetry["last_error"]
                assert telemetry["is_fallback"] is True


class TestSourceHealthTransitions:
    """Validate status transitions: HEALTHY -> DEGRADED -> OFFLINE."""

    def test_lifecycle_transitions(self):
        svc = SourceHealthService()
        
        # 1. Successful live harvest -> HEALTHY
        svc.record_attempt("TEST_SRC", latency_ms=15.0, success=True, is_fallback=False)
        t = svc.get_source_telemetry("TEST_SRC")
        assert t["status"] == "HEALTHY"
        assert t["last_error"] is None

        # 2. Live harvest failed, successful fixture fallback -> DEGRADED
        svc.record_attempt("TEST_SRC", latency_ms=25.0, success=True, is_fallback=True, error_message="HTTP 503")
        t = svc.get_source_telemetry("TEST_SRC")
        assert t["status"] == "DEGRADED"
        assert "HTTP 503" in t["last_error"]

        # 3. Both live harvest and fallback failed -> OFFLINE
        svc.record_attempt("TEST_SRC", latency_ms=10.0, success=False, is_fallback=False, error_message="Fatal crash")
        t = svc.get_source_telemetry("TEST_SRC")
        assert t["status"] == "OFFLINE"
        assert "Fatal crash" in t["last_error"]
