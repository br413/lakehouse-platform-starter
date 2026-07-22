#!/usr/bin/env python3
"""Route bronze ingest to DuckDB (local/CI) or Iceberg REST (Docker full stack)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    if os.environ.get("ICEBERG_CATALOG_URI"):
        subprocess.check_call([sys.executable, str(ROOT / "ingest_events_iceberg.py")])
        subprocess.check_call([sys.executable, str(ROOT / "sync_iceberg_to_duckdb.py")])
    else:
        subprocess.check_call([sys.executable, str(ROOT / "ingest_events.py")])


if __name__ == "__main__":
    main()
