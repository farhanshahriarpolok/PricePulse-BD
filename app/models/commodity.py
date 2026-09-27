"""
SQLAlchemy models for commodities and bilingual alias mappings.
"""

from datetime import datetime
from typing import List
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Commodity(Base):
    __tablename__ = "commodities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    bangla_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    default_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    aliases: Mapped[List["CommodityAlias"]] = relationship(
        "CommodityAlias", back_populates="commodity", cascade="all, delete-orphan"
    )
    observations: Mapped[List["PriceObservation"]] = relationship(
        "PriceObservation", back_populates="commodity"
    )

    def __repr__(self) -> str:
        return f"<Commodity(id={self.id}, canonical_name='{self.canonical_name}')>"


class CommodityAlias(Base):
    __tablename__ = "commodity_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="bn")
    confidence_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<CommodityAlias(alias='{self.alias}', commodity_id={self.commodity_id})>"
