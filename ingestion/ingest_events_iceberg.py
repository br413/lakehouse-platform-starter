#!/usr/bin/env python3
"""Ingest synthetic events into Iceberg bronze.events via REST catalog."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.iceberg_catalog import get_catalog  # noqa: E402

EVENT_TYPES = ("page_view", "signup", "purchase")
PAGES = ("/home", "/pricing", "/docs", "/blog")
TABLE = "bronze.events"


def build_batch(row_count: int = 3) -> pa.Table:
    now = datetime.now(timezone.utc)
    rows = {
        "id": [],
        "event_type": [],
        "event_timestamp": [],
        "user_id": [],
        "payload": [],
    }
    for i in range(row_count):
        event_type = EVENT_TYPES[i % len(EVENT_TYPES)]
        payload = {"page": PAGES[i % len(PAGES)]} if event_type == "page_view" else {"source": "iceberg_ingest"}
        rows["id"].append(f"evt-{uuid.uuid4().hex[:8]}")
        rows["event_type"].append(event_type)
        rows["event_timestamp"].append(now)
        rows["user_id"].append(f"user-{100 + i}")
        rows["payload"].append(json.dumps(payload))

    return pa.table(rows)


def main() -> None:
    catalog = get_catalog()
    if not catalog.table_exists(("bronze", "events")):
        init_script = ROOT / "storage" / "iceberg" / "scripts" / "init_catalog.py"
        subprocess.check_call([sys.executable, str(init_script)])

    table = catalog.load_table(("bronze", "events"))
    batch = build_batch()
    table.append(batch)
    print(f"Ingested {batch.num_rows} rows into {TABLE} (Iceberg REST catalog)")


if __name__ == "__main__":
    main()
