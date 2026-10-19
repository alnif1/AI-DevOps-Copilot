
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    log_text: str = Field(min_length=1, max_length=50_000)
    service_name: str = Field(default="unknown-service", max_length=100)
    environment: str = Field(default="local", max_length=50)


class IncidentReport(BaseModel):
    service_name: str
    environment: str
    severity: Literal["low", "medium", "high", "critical"]
    summary: str
    likely_causes: list[str]
    recommendations: list[str]
    evidence: list[str]
    matched_patterns: list[str]


class IncidentHistoryItem(BaseModel):
    id: UUID
    created_at: datetime
    logs: str
    report: IncidentReport
    alert_fingerprint: str | None = None
    alert_status: Literal["firing", "resolved"] | None = None
    alert_started_at: datetime | None = None
    alert_ended_at: datetime | None = None


class AlertmanagerAlert(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["firing", "resolved"]
    labels: dict[str, str]
    annotations: dict[str, str] = Field(default_factory=dict)
    starts_at: datetime = Field(alias="startsAt")
    ends_at: datetime | None = Field(default=None, alias="endsAt")
    generator_url: str | None = Field(default=None, alias="generatorURL")
    fingerprint: str = Field(min_length=1)


class AlertmanagerWebhook(BaseModel):
    status: Literal["firing", "resolved"]
    alerts: list[AlertmanagerAlert] = Field(min_length=1)


class AlertmanagerAlertResult(BaseModel):
    fingerprint: str
    status: Literal["firing", "resolved"]
    incident_id: UUID | None
    created: bool


class AlertmanagerWebhookResponse(BaseModel):
    status: Literal["processed"] = "processed"
    alerts: list[AlertmanagerAlertResult]
