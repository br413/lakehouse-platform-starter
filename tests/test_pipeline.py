"""End-to-end pipeline smoke test (no Docker required)."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "transform" / "dbt"
DB_PATH = ROOT / "storage" / "warehouse" / "dev.duckdb"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    env = os.environ.copy()
    env["DUCKDB_PATH"] = str(DB_PATH)
    env["DBT_PROFILES_DIR"] = str(DBT_DIR)
    subprocess.run(cmd, check=True, cwd=cwd or ROOT, env=env)


class PipelineSmokeTest(unittest.TestCase):
    def test_pipeline_produces_mart_rows(self) -> None:
        if DB_PATH.exists():
            DB_PATH.unlink()

        run([sys.executable, "ingestion/run_ingest.py"])
        run(["dbt", "deps"], cwd=DBT_DIR)
        run(["dbt", "seed", "--target", "dev"], cwd=DBT_DIR)
        run(["dbt", "build", "--target", "dev"], cwd=DBT_DIR)
        run([sys.executable, "quality/run_checkpoint.py"])

        import duckdb

        conn = duckdb.connect(str(DB_PATH), read_only=True)
        count = conn.execute("select count(*) from main_marts.fct_daily_events").fetchone()[0]
        conn.close()
        self.assertGreater(count, 0, "Mart should have rows after pipeline run")


if __name__ == "__main__":
    unittest.main()
