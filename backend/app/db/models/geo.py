import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Text, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, utcnow


class GeoEvent(Base):
    __tablename__ = "geo_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_key: Mapped[str] = mapped_column(String(64), nullable=False)
    region_label: Mapped[str] = mapped_column(String(128), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    article_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_tone: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_themes: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    query_used: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class GeoRiskIndex(Base):
    __tablename__ = "geo_risk_index"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    gpr_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gpr_threat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gpr_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class GeoNewsArticle(Base):
    __tablename__ = "geo_news_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_key: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    source_country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
