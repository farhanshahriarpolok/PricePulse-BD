"""
SQLAlchemy models for geographic and administrative market hierarchies.
"""

from typing import List, Optional
from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    bangla_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    districts: Mapped[List["District"]] = relationship(
        "District", back_populates="division", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Division(name='{self.name}')>"


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    division_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("divisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bangla_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    division: Mapped["Division"] = relationship("Division", back_populates="districts")
    markets: Mapped[List["Market"]] = relationship(
        "Market", back_populates="district", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<District(name='{self.name}', division='{self.division_id}')>"


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    bangla_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    market_type: Mapped[str] = mapped_column(String(30), default="retail")  # wholesale, retail, online
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    district: Mapped["District"] = relationship("District", back_populates="markets")
    observations: Mapped[List["PriceObservation"]] = relationship(
        "PriceObservation", back_populates="market"
    )

    def __repr__(self) -> str:
        return f"<Market(name='{self.name}', type='{self.market_type}')>"
