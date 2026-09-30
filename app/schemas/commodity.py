"""
Pydantic response models for commodities and alias registries.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CommodityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    bangla_name: str
    category: str
    default_unit: str


class CommodityDetailOut(CommodityOut):
    aliases: List[str] = []


class CommodityListResponse(BaseModel):
    total: int
    items: List[CommodityOut]


class StorePriceOut(BaseModel):
    id: str
    source_code: str
    name_bn: str
    name_en: str
    price: Optional[float] = None
    unit: Optional[str] = None
    collection_status: str  # LIVE, FALLBACK, MODELED, STALE, UNAVAILABLE
    status_label_bn: str
    status_label_en: str
    is_live: bool
    is_fallback: bool
    url: str
    observation_date: Optional[str] = None
    raw_name: Optional[str] = None
    error_message: Optional[str] = None


class CommodityStoresResponse(BaseModel):
    commodity_id: int
    canonical_name: str
    bangla_name: str
    default_unit: str
    stores: List[StorePriceOut]

