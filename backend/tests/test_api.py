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


def alert_payload(status: str = "firing") -> dict:
    alert = {
        "status": status,
        "labels": {
            "alertname": "EndpointUnavailable",
            "service": "payments-api",
            "scope": "external",
            "severity": "critical",
            "instance": "https://api.example.test/health",
        },
        "annotations": {
            "summary": "Payments API is unavailable",
            "description": "The endpoint probe has failed.",
        },
        "startsAt": "2026-10-18T12:00:00Z",
        "fingerprint": "phase4-test-fingerprint",
        "generatorURL": "http://prometheus:9090/graph",
    }
    if status == "resolved":
        alert["endsAt"] = "2026-10-18T12:02:00Z"
    return {
        "receiver": "opspilot",
        "status": status,
        "alerts": [alert],
    }


def test_alertmanager_firing_creates_tracked_incident(client, monkeypatch):
    incident_id = UUID("1163d1ce-9269-4e0c-adc5-c39ee75208b9")
    process = Mock(
        return_value={
            "fingerprint": "phase4-test-fingerprint",
            "status": "firing",
            "incident_id": incident_id,
            "created": True,
        }
    )
    monkeypatch.setattr(main, "process_alert", process)

    response = client.post("/api/v1/alerts", json=alert_payload())

    assert response.status_code == 200
    assert response.json()["alerts"][0]["created"] is True
    assert response.json()["alerts"][0]["incident_id"] == str(incident_id)
    call = process.call_args.kwargs
    assert call["fingerprint"] == "phase4-test-fingerprint"
    assert call["status"] == "firing"
    assert call["report"]["service_name"] == "payments-api"
    assert call["report"]["severity"] == "critical"
    assert call["report"]["summary"] == "Payments API is unavailable"


def test_alertmanager_resolved_notification_is_forwarded(client, monkeypatch):
    incident_id = UUID("1163d1ce-9269-4e0c-adc5-c39ee75208b9")
    process = Mock(
        return_value={
            "fingerprint": "phase4-test-fingerprint",
            "status": "resolved",
            "incident_id": incident_id,
            "created": False,
        }
    )
    monkeypatch.setattr(main, "process_alert", process)

    response = client.post(
        "/api/v1/alerts",
        json=alert_payload(status="resolved"),
    )

    assert response.status_code == 200
    assert response.json()["alerts"][0]["status"] == "resolved"
    assert response.json()["alerts"][0]["created"] is False
    process.assert_called_once()
    assert process.call_args.kwargs["ends_at"] is not None


def test_alertmanager_rejects_alert_without_fingerprint(client, monkeypatch):
    process = Mock()
    monkeypatch.setattr(main, "process_alert", process)
    payload = alert_payload()
    del payload["alerts"][0]["fingerprint"]

    response = client.post("/api/v1/alerts", json=payload)

    assert response.status_code == 422
    process.assert_not_called()
