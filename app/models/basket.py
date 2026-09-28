"""
SQLAlchemy models for saved consumer bazaar baskets and personal inflation tracking.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SavedBasket(Base):
    __tablename__ = "saved_baskets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    bangla_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[List["SavedBasketItem"]] = relationship(
        "SavedBasketItem", back_populates="basket", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SavedBasket(id={self.id}, name='{self.name}')>"


class SavedBasketItem(Base):
    __tablename__ = "saved_basket_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    basket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saved_baskets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

    basket: Mapped["SavedBasket"] = relationship("SavedBasket", back_populates="items")
    commodity: Mapped["Commodity"] = relationship("Commodity")

    def __repr__(self) -> str:
        return f"<SavedBasketItem(basket_id={self.basket_id}, comm_id={self.commodity_id}, qty={self.quantity} {self.unit})>"
