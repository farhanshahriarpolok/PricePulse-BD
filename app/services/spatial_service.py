"""
Spatial market analytics service calculating geographic spreads, markups, and GeoJSON overlays.
"""

import json
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

        # Compute spread metrics
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

            spread_summary = LocationSpreadMetrics(
                cheapest_market=f"{cheapest.market_name} ({cheapest.district})",
                cheapest_price=cheapest.avg_price,
                highest_market=f"{highest.market_name} ({highest.district})",
                highest_price=highest.avg_price,
                absolute_spread_bdt=abs_spread,
                percentage_spread=pct_spread,
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


spatial_service = SpatialService()
