import os
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def get_connection() -> psycopg.Connection[dict[str, Any]]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set to connect to PostgreSQL.")
    return psycopg.connect(database_url, row_factory=dict_row)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                logs TEXT NOT NULL,
                report JSONB NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_tracking (
                fingerprint TEXT NOT NULL,
                starts_at TIMESTAMPTZ NOT NULL,
                incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
                status TEXT NOT NULL CHECK (status IN ('firing', 'resolved')),
                ends_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (fingerprint, starts_at)
            )
            """
        )


def create_incident(logs: str, report: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        return _insert_incident(connection, logs, report)


def _insert_incident(
    connection: psycopg.Connection[dict[str, Any]],
    logs: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    row = connection.execute(
        """
        INSERT INTO incidents (id, logs, report)
        VALUES (%s, %s, %s)
        RETURNING id, created_at, logs, report
        """,
        (uuid4(), logs, Jsonb(report)),
    ).fetchone()
    if row is None:
        raise RuntimeError("PostgreSQL did not return the saved incident.")
    return row


def process_alert(
    *,
    fingerprint: str,
    status: str,
    starts_at: datetime,
    ends_at: datetime | None,
    logs: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    if status not in {"firing", "resolved"}:
        raise ValueError(f"Unsupported alert status: {status}")

    with get_connection() as connection:
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (f"{fingerprint}:{starts_at.isoformat()}",),
        )
        tracked = connection.execute(
            """
            SELECT incident_id, status
            FROM alert_tracking
            WHERE fingerprint = %s AND starts_at = %s
            FOR UPDATE
            """,
            (fingerprint, starts_at),
        ).fetchone()

        if status == "firing":
            if tracked is not None and tracked["status"] == "firing":
                connection.execute(
                    """
                    UPDATE alert_tracking
                    SET updated_at = now()
                    WHERE fingerprint = %s AND starts_at = %s
                    """,
                    (fingerprint, starts_at),
                )
                return {
                    "fingerprint": fingerprint,
                    "status": "firing",
                    "incident_id": tracked["incident_id"],
                    "created": False,
                }

            incident = _insert_incident(connection, logs, report)
            connection.execute(
                """
                INSERT INTO alert_tracking
                    (fingerprint, starts_at, incident_id, status, ends_at)
                VALUES (%s, %s, %s, 'firing', NULL)
                ON CONFLICT (fingerprint, starts_at) DO UPDATE SET
                    incident_id = EXCLUDED.incident_id,
                    status = 'firing',
                    ends_at = NULL,
                    updated_at = now()
                """,
                (fingerprint, starts_at, incident["id"]),
            )
            return {
                "fingerprint": fingerprint,
                "status": "firing",
                "incident_id": incident["id"],
                "created": True,
            }

        if tracked is None:
            connection.execute(
                """
                INSERT INTO alert_tracking
                    (fingerprint, starts_at, status, ends_at)
                VALUES (%s, %s, 'resolved', COALESCE(%s, now()))
                """,
                (fingerprint, starts_at, ends_at),
            )
            incident_id = None
        else:
            connection.execute(
                """
                UPDATE alert_tracking
                SET status = 'resolved',
                    ends_at = COALESCE(%s, now()),
                    updated_at = now()
                WHERE fingerprint = %s AND starts_at = %s
                """,
                (ends_at, fingerprint, starts_at),
            )
            incident_id = tracked["incident_id"]

        return {
            "fingerprint": fingerprint,
            "status": "resolved",
            "incident_id": incident_id,
            "created": False,
        }


def list_incidents() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT incidents.id,
                   incidents.created_at,
                   incidents.logs,
                   incidents.report,
                   alert_tracking.fingerprint AS alert_fingerprint,
                   alert_tracking.status AS alert_status,
                   alert_tracking.starts_at AS alert_started_at,
                   alert_tracking.ends_at AS alert_ended_at
            FROM incidents
            LEFT JOIN alert_tracking ON alert_tracking.incident_id = incidents.id
            ORDER BY incidents.created_at DESC, incidents.id DESC
            """
        ).fetchall()
    return rows


def delete_incident(incident_id: UUID) -> bool:
    with get_connection() as connection:
        result = connection.execute(
            "DELETE FROM incidents WHERE id = %s",
            (incident_id,),
        )
        deleted = result.rowcount > 0
    return deleted


def delete_all_incidents() -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM alert_tracking")
        connection.execute("DELETE FROM incidents")
