
from typing import Literal

from pydantic import BaseModel, Field


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
