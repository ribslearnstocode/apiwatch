from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Monitor(Base):
    __tablename__ = "monitors"
    __table_args__ = (CheckConstraint("check_interval BETWEEN 30 AND 86400"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    check_interval: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MonitorResult(Base):
    __tablename__ = "monitor_results"
    __table_args__ = (
        Index("ix_results_monitor_time", "monitor_id", "checked_at"),
        CheckConstraint("response_time_ms >= 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    monitor_id: Mapped[int] = mapped_column(ForeignKey("monitors.id", ondelete="CASCADE"))
    status_code: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[float] = mapped_column(Float)
    is_success: Mapped[bool] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(String(500))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_monitor_time", "monitor_id", "started_at"),
        Index("uq_open_incident", "monitor_id", unique=True,
              postgresql_where=text("resolved_at IS NULL"), sqlite_where=text("resolved_at IS NULL")),
        CheckConstraint("resolved_at IS NULL OR resolved_at >= started_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    monitor_id: Mapped[int] = mapped_column(ForeignKey("monitors.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(String(500))
