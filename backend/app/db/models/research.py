import uuid
from datetime import date, datetime
from typing import Any
from sqlalchemy import String, Integer, Float, Boolean, Text, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, utcnow


class Thesis(Base):
    __tablename__ = "theses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(8), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    catalysts: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    invalidation_conditions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="completed")
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    evidence_items: Mapped[list["EvidenceItem"]] = relationship("EvidenceItem", back_populates="thesis", cascade="all, delete-orphan", order_by="EvidenceItem.sort_order")
    scenarios: Mapped[list["ResearchScenario"]] = relationship("ResearchScenario", back_populates="thesis", cascade="all, delete-orphan", order_by="ResearchScenario.sort_order")
    counter_arguments: Mapped[list["CounterArgument"]] = relationship("CounterArgument", back_populates="thesis", cascade="all, delete-orphan", order_by="CounterArgument.sort_order")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thesis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    series_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    obs_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    thesis: Mapped["Thesis"] = relationship("Thesis", back_populates="evidence_items")


class ResearchScenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thesis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    probability: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    trigger: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    thesis: Mapped["Thesis"] = relationship("Thesis", back_populates="scenarios")


class CounterArgument(Base):
    __tablename__ = "counter_arguments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thesis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False)
    argument: Mapped[str] = mapped_column(Text, nullable=False)
    strength: Mapped[str] = mapped_column(String(16), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    thesis: Mapped["Thesis"] = relationship("Thesis", back_populates="counter_arguments")
