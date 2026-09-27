"""
SQLAlchemy model for atomic time-series price observations.
"""

from datetime import datetime, date
from sqlalchemy import Integer, String, Float, DateTime, Date, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    market_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_name: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_price: Mapped[float] = mapped_column(Float, nullable=False)
    raw_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_price: Mapped[float] = mapped_column(Float, nullable=False)
    normalized_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    price_type: Mapped[str] = mapped_column(String(30), nullable=False)  # retail_avg, wholesale_avg, etc.
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    __table_args__ = (
        UniqueConstraint(
            "commodity_id",
            "market_id",
            "source_id",
            "observation_date",
            "price_type",
            name="uq_observation_record",
        ),
    )

    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="observations")
    market: Mapped["Market"] = relationship("Market", back_populates="observations")
    source: Mapped["Source"] = relationship("Source", back_populates="observations")

    def __repr__(self) -> str:
        return (
            f"<PriceObservation(commodity_id={self.commodity_id}, "
            f"market_id={self.market_id}, price={self.normalized_price}, "
            f"unit='{self.normalized_unit}', date={self.observation_date})>"
        )
