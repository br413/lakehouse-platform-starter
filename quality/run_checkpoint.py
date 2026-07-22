"""Great Expectations checkpoint for mart publish gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import great_expectations as gx
import pandas as pd

DEFAULT_DB = Path(__file__).resolve().parents[1] / "storage" / "warehouse" / "dev.duckdb"
MART_TABLE_DUCKDB = os.environ.get("MART_TABLE", "main_marts.fct_daily_events")


def _load_mart_dataframe() -> pd.DataFrame:
    target = os.environ.get("DBT_TARGET", "dev")

    if target == "iceberg":
        from trino.dbapi import connect

        host = os.environ.get("TRINO_HOST", "localhost")
        port = int(os.environ.get("TRINO_PORT", "8090"))
        conn = connect(host=host, port=port, user="dbt", catalog="iceberg", schema="marts")
        cur = conn.cursor()
        cur.execute("SELECT event_date, event_type, event_count, unique_users FROM fct_daily_events")
        rows = cur.fetchall()
        columns = [col[0] for col in cur.description]
        conn.close()
        return pd.DataFrame(rows, columns=columns)

    import duckdb

    path = Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    if not path.exists():
        raise FileNotFoundError(f"Warehouse not found: {path}. Run `make pipeline` first.")

    conn = duckdb.connect(str(path), read_only=True)
    df = conn.execute(f"select * from {MART_TABLE_DUCKDB}").fetchdf()
    conn.close()
    return df


def run_checkpoint() -> None:
    df = _load_mart_dataframe()

    if df.empty:
        raise ValueError("fct_daily_events is empty — quality gate failed")

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

    backend = os.environ.get("DBT_TARGET", "dev")
    print(f"Quality gate passed ({backend}): {len(df)} mart rows validated")


if __name__ == "__main__":
    run_checkpoint()
