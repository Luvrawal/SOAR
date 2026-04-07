from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlertCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    source: str = Field(..., min_length=2, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    description: str | None = Field(default=None, max_length=5000)
    raw_alert: dict | None = None
    created_by: int | None = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: str) -> str:
        return str(value).lower()


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    severity: str
    status: str
    playbook_status: str
    description: str | None
    raw_alert: dict | None
    playbook_result: dict | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    playbook_last_run_at: datetime | None
