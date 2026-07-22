#!/usr/bin/env python3
"""Sync Iceberg bronze.events into DuckDB for dbt transform (local bridge).

Production: replace with dbt-trino/spark reading Iceberg directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.iceberg_catalog import get_catalog  # noqa: E402
from ingestion.ingest_events import DEFAULT_DB, ensure_bronze_table, get_connection  # noqa: E402


def main() -> None:
    catalog = get_catalog()
    iceberg_table = catalog.load_table(("bronze", "events"))
    arrow_table = iceberg_table.scan().to_arrow()

    db_path = Path(__import__("os").environ.get("DUCKDB_PATH", DEFAULT_DB))
    with get_connection(db_path) as conn:
        ensure_bronze_table(conn)
        conn.execute("delete from bronze.events")
        if arrow_table.num_rows > 0:
            conn.register("_iceberg_events", arrow_table.to_pandas())
            conn.execute(
                """
                insert into bronze.events (id, event_type, event_timestamp, user_id, payload)
                select id, event_type, event_timestamp, user_id, payload
                from _iceberg_events
                """
            )
        total = conn.execute("select count(*) from bronze.events").fetchone()[0]

    print(f"Synced {total} rows from Iceberg bronze.events → DuckDB ({db_path})")


if __name__ == "__main__":
    main()
