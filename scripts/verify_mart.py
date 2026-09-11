"""Print mart row count and a short sample. Exit 1 if empty."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "storage" / "warehouse" / "dev.duckdb"


def main() -> int:
    path = Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    if not path.exists():
        print(f"Warehouse not found: {path}", file=sys.stderr)
        return 1

    conn = duckdb.connect(str(path), read_only=True)
    count = conn.execute("select count(*) from main_marts.fct_daily_events").fetchone()[0]
    sample = conn.execute(
        """
        select event_date, event_type, event_count
        from main_marts.fct_daily_events
        order by event_date, event_type
        limit 5
        """
    ).fetchall()
    conn.close()

    print(f"MART_ROWS={count}")
    for row in sample:
        print(f"  {row[0]} | {row[1]} | {row[2]}")

    return 0 if count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
