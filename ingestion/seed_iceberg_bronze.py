#!/usr/bin/env python3
"""Load dbt seed CSV into Iceberg bronze.events (Trino/dbt-trino path)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingestion.iceberg_catalog import get_catalog  # noqa: E402

SEED_PATH = ROOT / "transform" / "dbt" / "seeds" / "events.csv"
TABLE = ("bronze", "events")


def main() -> None:
    if not SEED_PATH.exists():
        raise FileNotFoundError(f"Seed file not found: {SEED_PATH}")

    init_script = ROOT / "storage" / "iceberg" / "scripts" / "init_catalog.py"
    subprocess = __import__("subprocess")
    subprocess.check_call([sys.executable, str(init_script)])

    df = pd.read_csv(SEED_PATH)
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True)
    arrow = pa.Table.from_pandas(df, preserve_index=False)

    catalog = get_catalog()
    table = catalog.load_table(TABLE)
    table.overwrite(arrow)
    print(f"Seeded {arrow.num_rows} rows into {'{}.{}'.format(*TABLE)} (Iceberg overwrite)")


if __name__ == "__main__":
    main()
