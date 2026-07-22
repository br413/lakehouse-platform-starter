#!/usr/bin/env python3
"""Simulate bronze ingest: append synthetic events to the DuckDB bronze table.

Production: replace with Meltano/Airbyte sync into Iceberg bronze.events.
Local dev: writes to the same DuckDB file dbt uses as its bronze source.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

DEFAULT_DB = Path(__file__).resolve().parents[1] / "storage" / "warehouse" / "dev.duckdb"
EVENT_TYPES = ("page_view", "signup", "purchase")
PAGES = ("/home", "/pricing", "/docs", "/blog")


def get_connection(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    path = db_path or Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def ensure_bronze_table(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("create schema if not exists bronze")
    conn.execute(
        """
        create table if not exists bronze.events (
            id varchar,
            event_type varchar,
            event_timestamp timestamp,
            user_id varchar,
            payload varchar
        )
        """
    )


def ingest_batch(conn: duckdb.DuckDBPyConnection, row_count: int = 3) -> int:
    """Insert synthetic events for the current UTC day."""
    now = datetime.now(timezone.utc)
    rows = []
    for _ in range(row_count):
        event_type = EVENT_TYPES[len(rows) % len(EVENT_TYPES)]
        payload = {"page": PAGES[len(rows) % len(PAGES)]} if event_type == "page_view" else {"source": "ingest"}
        rows.append(
            (
                f"evt-{uuid.uuid4().hex[:8]}",
                event_type,
                now,
                f"user-{100 + len(rows)}",
                json.dumps(payload),
            )
        )

    conn.executemany(
        "insert into bronze.events values (?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def main() -> None:
    db_path = Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    with get_connection(db_path) as conn:
        ensure_bronze_table(conn)
        inserted = ingest_batch(conn)
        total = conn.execute("select count(*) from bronze.events").fetchone()[0]
    print(f"Ingested {inserted} events into {db_path} (total rows: {total})")


if __name__ == "__main__":
    main()
