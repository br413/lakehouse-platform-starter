"""Great Expectations checkpoint for mart publish gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb
import great_expectations as gx

DEFAULT_DB = Path(__file__).resolve().parents[1] / "storage" / "warehouse" / "dev.duckdb"
MART_TABLE = os.environ.get("MART_TABLE", "main_marts.fct_daily_events")


def run_checkpoint(db_path: Path | None = None) -> None:
    path = db_path or Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    if not path.exists():
        raise FileNotFoundError(f"Warehouse not found: {path}. Run `make pipeline` first.")

    conn = duckdb.connect(str(path), read_only=True)
    df = conn.execute(f"select * from {MART_TABLE}").fetchdf()
    conn.close()

    if df.empty:
        raise ValueError(f"{MART_TABLE} is empty — quality gate failed")

    context = gx.get_context(mode="ephemeral")
    suite = context.suites.add(gx.ExpectationSuite(name="mart_quality"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="event_date"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="event_count"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="event_count", min_value=1)
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="unique_users", min_value=1)
    )

    data_source = context.data_sources.add_pandas(name="mart")
    asset = data_source.add_dataframe_asset(name="fct_daily_events")
    batch_definition = asset.add_batch_definition_whole_dataframe(name="full")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    validation = batch.validate(suite)

    if not validation.success:
        print(validation.to_json_dict(), file=sys.stderr)
        raise SystemExit(1)

    print(f"Quality gate passed: {len(df)} mart rows validated")


if __name__ == "__main__":
    run_checkpoint()
