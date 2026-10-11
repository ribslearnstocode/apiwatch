from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from .security import validate_url


class MonitorInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(max_length=2048)
    check_interval: int = Field(default=60, ge=30, le=86400)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value):
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value.strip()

    @field_validator("url")
    @classmethod
    def public_url(cls, value):
        return validate_url(value)


class UTCModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", check_fields=False)
    def serialize_utc(self, value):
        if isinstance(value, datetime):
            return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
        return value


class MonitorOut(UTCModel):
    id: int
    name: str
    url: str
    check_interval: int
    is_active: bool
    created_at: datetime


class ResultOut(UTCModel):
    id: int
    monitor_id: int
    status_code: int | None
    response_time_ms: float
    is_success: bool
    error_message: str | None
    checked_at: datetime


class IncidentOut(UTCModel):
    id: int
    monitor_id: int
    started_at: datetime
    resolved_at: datetime | None
    description: str


class MonitorStats(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    check_interval: int
    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percentage: float | None
    avg_response_time: float | None
    min_response_time: float | None
    max_response_time: float | None
    incident_count: int
    latest_response_time: float | None
    last_checked: str | None
    status: Literal["healthy", "unhealthy", "not_yet_checked", "inactive"]


class Summary(BaseModel):
    total_monitors: int
    active_monitors: int
    inactive_monitors: int
    healthy_monitors: int
    unhealthy_monitors: int
    average_response_time: float | None
    successful_checks: int
    failed_checks: int
    monitors: list[MonitorStats]
