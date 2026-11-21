import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, utcnow


class MacroSeries(Base):
    __tablename__ = "macro_series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="macro")
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    units: Mapped[str] = mapped_column(String(128), nullable=False)
    frequency: Mapped[str] = mapped_column(String(64), nullable=False, default="Daily")
    seasonal_adjustment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNAVAILABLE")
    stale_after_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=72)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    observations: Mapped[list["MacroObservation"]] = relationship(
        "MacroObservation", back_populates="series", cascade="all, delete-orphan"
    )


class MacroObservation(Base):
    __tablename__ = "macro_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    macro_series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("macro_series.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), nullable=False)
    units: Mapped[str] = mapped_column(String(128), nullable=False)

    series: Mapped["MacroSeries"] = relationship("MacroSeries", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("macro_series_id", "date", name="uq_macro_obs_series_date"),
    )
