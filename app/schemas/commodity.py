"""
Pydantic response models for commodities and alias registries.
"""

from typing import List
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
