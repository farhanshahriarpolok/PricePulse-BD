from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import Integer, String, Float, Date, DateTime, UniqueConstraint
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


class SourceHealthLog(Base):
    """
    Persistent daily health, availability, and latency telemetry for upstream sources.
    Guarantees deterministic aggregation, idempotency via UNIQUE(source_name, date),
    and survival across application restarts.
    """
    __tablename__ = "source_health_logs"
    __table_args__ = (
        UniqueConstraint("source_name", "date", name="uq_source_health_logs_source_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_checks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_checks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_checks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SourceHealthLog(source='{self.source_name}', date={self.date}, "
            f"avail={self.availability_percent}%, checks={self.total_checks})>"
        )
