import os
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


def create_incident(logs: str, report: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
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


def list_incidents() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, logs, report
            FROM incidents
            ORDER BY created_at DESC, id DESC
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
        connection.execute("DELETE FROM incidents")
