import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, BigInteger, Float, Boolean, Text, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, utcnow


class CotInstrument(Base):
    __tablename__ = "cot_instruments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cftc_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_series_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    reports: Mapped[list["CotReport"]] = relationship("CotReport", back_populates="instrument", cascade="all, delete-orphan")


class CotReport(Base):
    __tablename__ = "cot_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cot_instruments.id", ondelete="CASCADE"), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_interest: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    noncomm_long: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    noncomm_short: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    noncomm_spread: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    comm_long: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    comm_short: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    net_noncomm: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    net_noncomm_pct_oi: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_noncomm_long: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    change_noncomm_short: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    instrument: Mapped["CotInstrument"] = relationship("CotInstrument", back_populates="reports")

    __table_args__ = (
        UniqueConstraint("instrument_id", "report_date", name="uq_cot_instrument_date"),
    )


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)  # price_threshold | cot_extreme
    series_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cftc_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)  # above | below
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    events: Mapped[list["AlertEvent"]] = relationship("AlertEvent", back_populates="rule", cascade="all, delete-orphan")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    value_at_trigger: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rule: Mapped["AlertRule"] = relationship("AlertRule", back_populates="events")
