"""
SQLAlchemy model for data publishers and source registries.
"""

from typing import List, Optional
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), default="government")
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)

    observations: Mapped[List["PriceObservation"]] = relationship(
        "PriceObservation", back_populates="source"
    )

    def __repr__(self) -> str:
        return f"<Source(code='{self.code}', reliability={self.reliability_score})>"
