"""
Spatial market analytics service calculating geographic spreads, markups, and GeoJSON overlays.
"""

import json
import math
from datetime import date
from typing import Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.commodity import Commodity
from app.models.location import Division, District, Market
from app.models.observation import PriceObservation
from app.services.normalizer import CommodityNormalizer, commodity_normalizer
from app.schemas.spatial import (
    MarketPricePoint,
    DistrictAggregate,
    LocationSpreadMetrics,
    GeoSpatialPulseResponse,
    LocationHierarchyDivision,
    LocationHierarchyDistrict,
    LocationHierarchyMarket,
    LocationHierarchyResponse,
    ArbitrageRoute,
    SpatialArbitrageResponse,
)


class SpatialService:
    """Computes inter-market spatial spreads, regional disparities, and GeoJSON structures."""

    def __init__(self, normalizer: Optional[CommodityNormalizer] = None):
        self.normalizer = normalizer or commodity_normalizer
        self.geojson_path = settings.data_dir / "geo" / "bangladesh_districts_simplified.json"

    def resolve_commodity(self, db: Session, commodity_identifier: str) -> Optional[Commodity]:
        """Resolve either an integer ID, canonical name, or localized alias to Commodity model."""
        raw_str = str(commodity_identifier).strip()
        
        # 1. Integer ID check
        if raw_str.isdigit():
            stmt = select(Commodity).where(Commodity.id == int(raw_str))
            comm = db.scalars(stmt).first()
            if comm:
                return comm

        # 2. Taxonomy normalizer resolution (e.g., 'onion_local' -> 'onion local')
        sanitized = raw_str.replace("_", " ").replace("-", " ")
        match = self.normalizer.resolve_commodity(sanitized)
        if match:
            stmt = select(Commodity).where(Commodity.canonical_name == match.canonical_name)
            comm = db.scalars(stmt).first()
            if comm:
                return comm

        # 3. Direct DB ILIKE check
        stmt = select(Commodity).where(
            (Commodity.canonical_name.ilike(f"%{sanitized}%"))
            | (Commodity.bangla_name.ilike(f"%{sanitized}%"))
        )
        return db.scalars(stmt).first()

    def get_spatial_spread(
        self,
        db: Session,
        commodity_identifier: str,
        target_date: Optional[date] = None,
    ) -> Optional[GeoSpatialPulseResponse]:
        """Calculate market spread metrics and attach GeoJSON district overlays."""
        commodity = self.resolve_commodity(db, commodity_identifier)
        if not commodity:
            return None

        # Determine effective date: target_date or the latest available date for this commodity
        if target_date:
            eff_date = target_date
        else:
            latest_date_stmt = (
                select(func.max(PriceObservation.observation_date))
                .where(PriceObservation.commodity_id == commodity.id)
            )
            eff_date = db.scalar(latest_date_stmt) or date.today()

        # Query all observations for this commodity on the effective date
        stmt = (
            select(
                Market.id.label("market_id"),
                Market.name.label("market_name"),
                Market.market_type,
                Market.latitude,
                Market.longitude,
                District.name.label("district_name"),
                Division.name.label("division_name"),
                func.avg(PriceObservation.normalized_price).label("avg_price"),
                func.avg(PriceObservation.confidence_score).label("avg_conf"),
            )
            .join(Market, PriceObservation.market_id == Market.id)
            .join(District, Market.district_id == District.id)
            .join(Division, District.division_id == Division.id)
            .where(
                PriceObservation.commodity_id == commodity.id,
                PriceObservation.observation_date == eff_date,
            )
            .group_by(
                Market.id,
                Market.name,
                Market.market_type,
                Market.latitude,
                Market.longitude,
                District.name,
                Division.name,
            )
            .order_by(func.avg(PriceObservation.normalized_price).asc())
        )
        market_rows = db.execute(stmt).all()

        market_points: List[MarketPricePoint] = []
        for row in market_rows:
            market_points.append(
                MarketPricePoint(
                    market_id=row.market_id,
                    market_name=row.market_name,
                    market_type=row.market_type,
                    district=row.district_name,
                    division=row.division_name,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    avg_price=round(float(row.avg_price), 2),
                    unit=commodity.default_unit,
                    confidence_score=round(float(row.avg_conf or 0.85), 3),
                )
            )

        # Aggregate district summaries
        district_map: Dict[str, List[float]] = {}
        district_meta: Dict[str, dict] = {}

        for pt in market_points:
            d_name = pt.district
            if d_name not in district_map:
                district_map[d_name] = []
                district_meta[d_name] = {
                    "division": pt.division,
                    "latitude": pt.latitude,
                    "longitude": pt.longitude,
                }
            district_map[d_name].append(pt.avg_price)

        district_aggregates: List[DistrictAggregate] = []
        for d_name, prices in district_map.items():
            meta = district_meta[d_name]
            district_aggregates.append(
                DistrictAggregate(
                    district=d_name,
                    division=meta["division"],
                    avg_price=round(sum(prices) / len(prices), 2),
                    min_price=round(min(prices), 2),
                    max_price=round(max(prices), 2),
                    market_count=len(prices),
                    latitude=meta["latitude"],
                    longitude=meta["longitude"],
                )
            )

        # Compute spread metrics and Spatial Price Dispersion Index D(t)
        spread_summary = LocationSpreadMetrics()
        if market_points:
            cheapest = market_points[0]
            highest = market_points[-1]
            abs_spread = round(highest.avg_price - cheapest.avg_price, 2)
            pct_spread = (
                round((abs_spread / cheapest.avg_price) * 100.0, 2)
                if cheapest.avg_price > 0
                else 0.0
            )

            prices = [pt.avg_price for pt in market_points]
            n_pts = len(prices)
            mean_p = sum(prices) / n_pts
            variance = sum((p - mean_p) ** 2 for p in prices) / n_pts
            std_dev = math.sqrt(variance)
            dispersion_index = round(std_dev / mean_p, 4) if mean_p > 0 else 0.0

            spread_summary = LocationSpreadMetrics(
                cheapest_market=f"{cheapest.market_name} ({cheapest.district})",
                cheapest_price=cheapest.avg_price,
                highest_market=f"{highest.market_name} ({highest.district})",
                highest_price=highest.avg_price,
                absolute_spread_bdt=abs_spread,
                percentage_spread=pct_spread,
                spatial_dispersion_index=dispersion_index,
                mean_market_price=round(mean_p, 2),
                std_dev_price=round(std_dev, 2),
            )

        # Generate Leaflet-ready GeoJSON feature collection
        geojson_features = self._build_geojson(district_aggregates, commodity.default_unit)

        return GeoSpatialPulseResponse(
            commodity_id=commodity.id,
            canonical_name=commodity.canonical_name,
            bangla_name=commodity.bangla_name,
            unit=commodity.default_unit,
            date=eff_date,
            spread_summary=spread_summary,
            districts=district_aggregates,
            markets=market_points,
            geojson_feature_collection=geojson_features,
        )

    def _build_geojson(
        self, district_aggregates: List[DistrictAggregate], unit: str
    ) -> Optional[dict]:
        """Enrich simplified Bangladesh GeoJSON with live price properties."""
        if not self.geojson_path.exists():
            return None

        with open(self.geojson_path, "r", encoding="utf-8") as f:
            geojson = json.load(f)

        price_by_district = {d.district.lower(): d for d in district_aggregates}

        for feature in geojson.get("features", []):
            f_name = feature.get("properties", {}).get("name", "").lower()
            if f_name in price_by_district:
                d_agg = price_by_district[f_name]
                feature["properties"]["has_data"] = True
                feature["properties"]["avg_price"] = d_agg.avg_price
                feature["properties"]["min_price"] = d_agg.min_price
                feature["properties"]["max_price"] = d_agg.max_price
                feature["properties"]["market_count"] = d_agg.market_count
                feature["properties"]["unit"] = unit
            else:
                feature["properties"]["has_data"] = False
                feature["properties"]["avg_price"] = None

        return geojson

    def get_location_hierarchy(self, db: Session) -> LocationHierarchyResponse:
        """Retrieve the complete spatial hierarchy (Divisions -> Districts -> Markets)."""
        stmt = (
            select(Division)
            .options(
                selectinload(Division.districts).selectinload(District.markets)
            )
            .order_by(Division.id)
        )
        divisions = list(db.scalars(stmt).all())

        div_outs: List[LocationHierarchyDivision] = []
        total_districts = 0
        total_markets = 0

        for div in divisions:
            dist_outs: List[LocationHierarchyDistrict] = []
            for dist in div.districts:
                mkt_outs = [
                    LocationHierarchyMarket(
                        id=m.id,
                        name=m.name,
                        bangla_name=m.bangla_name,
                        market_type=m.market_type,
                        latitude=m.latitude,
                        longitude=m.longitude,
                    )
                    for m in dist.markets
                ]
                total_markets += len(mkt_outs)
                dist_outs.append(
                    LocationHierarchyDistrict(
                        id=dist.id,
                        name=dist.name,
                        bangla_name=dist.bangla_name,
                        markets=mkt_outs,
                    )
                )
            total_districts += len(dist_outs)
            div_outs.append(
                LocationHierarchyDivision(
                    id=div.id,
                    name=div.name,
                    bangla_name=div.bangla_name,
                    districts=dist_outs,
                )
            )

        return LocationHierarchyResponse(
            total_divisions=len(div_outs),
            total_districts=total_districts,
            total_markets=total_markets,
            divisions=div_outs,
        )

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance in kilometers scaled by road circuity factor (1.25)."""
        r = 6371.0  # Earth radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        direct_dist = r * c
        return round(direct_dist * 1.25, 1)

    def get_spatial_arbitrage(
        self,
        db: Session,
        commodity_identifier: str,
        target_date: Optional[date] = None,
    ) -> Optional[SpatialArbitrageResponse]:
        """
        Evaluate freight-adjusted inter-district spatial arbitrage opportunities
        between surplus production hubs and deficit metropolitan consumption hubs.
        """
        commodity = self.resolve_commodity(db, commodity_identifier)
        if not commodity:
            return None

        # Determine effective date
        if target_date:
            eff_date = target_date
        else:
            latest_date_stmt = (
                select(func.max(PriceObservation.observation_date))
                .where(PriceObservation.commodity_id == commodity.id)
            )
            eff_date = db.scalar(latest_date_stmt) or date.today()

        # Query district level average prices
        stmt = (
            select(
                District.name.label("district_name"),
                Market.name.label("market_name"),
                Market.latitude,
                Market.longitude,
                func.avg(PriceObservation.normalized_price).label("avg_price"),
            )
            .join(Market, PriceObservation.market_id == Market.id)
            .join(District, Market.district_id == District.id)
            .where(
                PriceObservation.commodity_id == commodity.id,
                PriceObservation.observation_date == eff_date,
            )
            .group_by(District.name, Market.name, Market.latitude, Market.longitude)
        )
        obs_rows = db.execute(stmt).all()

        district_nodes = {}
        for row in obs_rows:
            d_name = row.district_name
            if d_name not in district_nodes or row.avg_price < district_nodes[d_name]["price"]:
                district_nodes[d_name] = {
                    "district": d_name,
                    "market": row.market_name,
                    "lat": float(row.latitude or 23.8),
                    "lon": float(row.longitude or 90.4),
                    "price": round(float(row.avg_price), 2),
                }

        # Baseline benchmark price for this commodity
        base_benchmark = (
            db.scalar(
                select(func.avg(PriceObservation.normalized_price))
                .where(
                    PriceObservation.commodity_id == commodity.id,
                    PriceObservation.observation_date == eff_date,
                )
            )
            or 100.0
        )
        base_benchmark = float(base_benchmark)

        # Canonical agricultural geography hubs in Bangladesh
        canonical_hubs = {
            "Bogura": {"district": "Bogura", "market": "Raja Bazar Bogura", "lat": 24.8465, "lon": 89.3770, "type": "production", "price_factor": 0.82},
            "Rangpur": {"district": "Rangpur", "market": "City Bazar Rangpur", "lat": 25.7439, "lon": 89.2752, "type": "production", "price_factor": 0.80},
            "Jashore": {"district": "Jashore", "market": "Boro Bazar Jashore", "lat": 23.1664, "lon": 89.2081, "type": "production", "price_factor": 0.85},
            "Rajshahi": {"district": "Rajshahi", "market": "Masterpara Wholesale", "lat": 24.3636, "lon": 88.6241, "type": "production", "price_factor": 0.84},
            "Dinajpur": {"district": "Dinajpur", "market": "Bahadur Bazar Dinajpur", "lat": 25.6217, "lon": 88.6355, "type": "production", "price_factor": 0.79},
            "Dhaka": {"district": "Dhaka", "market": "Karwan Bazar", "lat": 23.8103, "lon": 90.4125, "type": "consumption", "price_factor": 1.00},
            "Chattogram": {"district": "Chattogram", "market": "Khatunganj", "lat": 22.3569, "lon": 91.7832, "type": "consumption", "price_factor": 1.08},
            "Sylhet": {"district": "Sylhet", "market": "Sobhanighat Wholesale Arat", "lat": 24.8949, "lon": 91.8687, "type": "consumption", "price_factor": 1.12},
        }

        # Merge actual DB prices or calibrated prices into active hubs
        for h_name, hub_info in canonical_hubs.items():
            if h_name in district_nodes:
                hub_info["price"] = district_nodes[h_name]["price"]
                hub_info["market"] = district_nodes[h_name]["market"]
            else:
                hub_info["price"] = round(base_benchmark * hub_info["price_factor"], 2)

        prod_hubs = [h for h in canonical_hubs.values() if h["type"] == "production"]
        cons_hubs = [h for h in canonical_hubs.values() if h["type"] == "consumption"]

        # Calculate routes and freight arbitrage
        routes: List[ArbitrageRoute] = []
        all_prices = [h["price"] for h in canonical_hubs.values()]
        mean_p = sum(all_prices) / len(all_prices)
        variance = sum((p - mean_p) ** 2 for p in all_prices) / len(all_prices)
        std_p = math.sqrt(variance)
        dispersion_index = round(std_p / mean_p, 4) if mean_p > 0 else 0.0
        cv_pct = round(dispersion_index * 100.0, 2)

        for src in prod_hubs:
            for dest in cons_hubs:
                dist_km = self.haversine_distance(src["lat"], src["lon"], dest["lat"], dest["lon"])
                # Freight cost model: 1.50 BDT fixed loading overhead + 0.018 BDT per kg per km
                freight_cost = round(1.50 + dist_km * 0.018, 2)
                gross_spread = round(dest["price"] - src["price"], 2)
                net_margin = round(gross_spread - freight_cost, 2)
                invested = src["price"] + freight_cost
                roi_pct = round((net_margin / invested) * 100.0, 2) if invested > 0 else 0.0

                if net_margin >= 6.0:
                    feasibility = "Highly Feasible"
                elif net_margin >= 2.0:
                    feasibility = "Marginal"
                else:
                    feasibility = "Infeasible (Transport Barrier)"

                routes.append(
                    ArbitrageRoute(
                        source_district=src["district"],
                        destination_district=dest["district"],
                        source_market=src["market"],
                        destination_market=dest["market"],
                        source_price=src["price"],
                        destination_price=dest["price"],
                        gross_spread_bdt=gross_spread,
                        distance_km=dist_km,
                        estimated_freight_cost_bdt=freight_cost,
                        net_arbitrage_margin_bdt=net_margin,
                        roi_percentage=roi_pct,
                        economic_feasibility=feasibility,
                    )
                )

        # Sort routes by net arbitrage margin descending
        routes.sort(key=lambda r: r.net_arbitrage_margin_bdt, reverse=True)

        top_route = routes[0] if routes else None
        if top_route and top_route.net_arbitrage_margin_bdt > 5.0:
            rec = (
                f"Strong spatial arbitrage corridor identified: Transport from {top_route.source_district} "
                f"({top_route.source_market}) to {top_route.destination_district} ({top_route.destination_market}) "
                f"yields a net margin of BDT {top_route.net_arbitrage_margin_bdt:.2f}/{commodity.default_unit} "
                f"(ROI: {top_route.roi_percentage:.1f}%) after covering BDT {top_route.estimated_freight_cost_bdt:.2f} freight."
            )
        else:
            rec = "Spatial price dispersion is in competitive equilibrium with minimal spatial arbitrage surplus."

        return SpatialArbitrageResponse(
            commodity_id=commodity.id,
            canonical_name=commodity.canonical_name,
            bangla_name=commodity.bangla_name,
            unit=commodity.default_unit,
            observation_date=eff_date,
            spatial_dispersion_index=dispersion_index,
            inter_district_cv_pct=cv_pct,
            production_hubs=[h["district"] for h in prod_hubs],
            consumption_hubs=[h["district"] for h in cons_hubs],
            routes=routes[:12],
            recommendation=rec,
        )


spatial_service = SpatialService()
