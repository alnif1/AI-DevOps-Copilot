from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "initialize_database", lambda: None)
    with TestClient(main.app) as test_client:
        yield test_client


def saved_incident(logs: str = "Database connection failed") -> dict:
    return {
        "id": UUID("b8b14b89-30f4-482a-9792-d255d880a4d4"),
        "created_at": datetime(2026, 10, 17, tzinfo=timezone.utc),
        "logs": logs,
        "report": {
            "service_name": "payment-api",
            "environment": "local",
            "severity": "high",
            "summary": "Possible database connectivity failure.",
            "likely_causes": ["The database may be unavailable."],
            "recommendations": ["Check database health and availability."],
            "evidence": [logs],
            "matched_patterns": ["database_connection"],
        },
    }


def test_analyze_saves_and_returns_incident(client, monkeypatch):
    saved = saved_incident()
    create = Mock(return_value=saved)
    monkeypatch.setattr(main, "create_incident", create)

    response = client.post(
        "/api/v1/analyze",
        json={
            "log_text": "Database connection failed",
            "service_name": "payment-api",
            "environment": "local",
        },
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "high"
    create.assert_called_once()


def test_history_returns_saved_incidents(client, monkeypatch):
    saved = saved_incident()
    monkeypatch.setattr(main, "list_incidents", lambda: [saved])

    response = client.get("/api/v1/history")

    assert response.status_code == 200
    assert response.json()[0]["logs"] == saved["logs"]


def test_delete_incident_returns_not_found_for_unknown_id(client, monkeypatch):
    monkeypatch.setattr(main, "delete_incident", lambda _: False)

    response = client.delete(
        "/api/v1/history/b8b14b89-30f4-482a-9792-d255d880a4d4"
    )

    assert response.status_code == 404


def test_clear_history_returns_no_content(client, monkeypatch):
    clear = Mock()
    monkeypatch.setattr(main, "delete_all_incidents", clear)

    response = client.delete("/api/v1/history")

    assert response.status_code == 204
    clear.assert_called_once_with()
