"""Daily lakehouse pipeline: ingest → transform → quality gate.

Supports two transform backends via DBT_TARGET:
  - dev (default): DuckDB — fast local/CI path
  - iceberg: Trino + Iceberg — native lakehouse path (Docker)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from cosmos import DbtTaskGroup, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.constants import ExecutionMode, TestBehavior

REPO_ROOT = Path("/opt/lakehouse")
DBT_DIR = REPO_ROOT / "transform" / "dbt"
DUCKDB_PATH = REPO_ROOT / "storage" / "warehouse" / "dev.duckdb"

DBT_TARGET = os.environ.get("DBT_TARGET", "dev")
TRINO_HOST = os.environ.get("TRINO_HOST", "trino")
TRINO_PORT = os.environ.get("TRINO_PORT", "8080")

ENV_EXPORTS = (
    f"export DBT_TARGET={DBT_TARGET} "
    f"&& export DUCKDB_PATH={DUCKDB_PATH} "
    f"&& export DBT_PROFILES_DIR={DBT_DIR} "
    f"&& export ICEBERG_CATALOG_URI={os.environ.get('ICEBERG_CATALOG_URI', '')} "
    f"&& export ICEBERG_S3_ENDPOINT={os.environ.get('ICEBERG_S3_ENDPOINT', '')} "
    f"&& export TRINO_HOST={TRINO_HOST} "
    f"&& export TRINO_PORT={TRINO_PORT} "
)

profile_config = ProfileConfig(
    profile_name="lakehouse_platform",
    target_name=DBT_TARGET,
    profiles_yml_filepath=DBT_DIR / "profiles.yml",
)

project_config = ProjectConfig(
    dbt_project_path=str(DBT_DIR),
    env_vars={
        "DUCKDB_PATH": str(DUCKDB_PATH),
        "TRINO_HOST": TRINO_HOST,
        "TRINO_PORT": TRINO_PORT,
        "DBT_TARGET": DBT_TARGET,
    },
)

execution_config = ExecutionConfig(
    execution_mode=ExecutionMode.VIRTUALENV,
    virtualenv_dir=str(REPO_ROOT / f".dbt_venv_{DBT_TARGET}"),
)

render_config = RenderConfig(
    select=["path:models/staging", "path:models/intermediate", "path:models/marts"],
    test_behavior=TestBehavior.BUILD,
)

DBT_REQUIREMENTS = ["dbt-trino>=1.8.0"] if DBT_TARGET == "iceberg" else ["dbt-duckdb>=1.9.0"]

operator_env = {
    "DBT_PROFILES_DIR": str(DBT_DIR),
    "DBT_TARGET": DBT_TARGET,
    "TRINO_HOST": TRINO_HOST,
    "TRINO_PORT": TRINO_PORT,
}
if DBT_TARGET == "dev":
    operator_env["DUCKDB_PATH"] = str(DUCKDB_PATH)

default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="lakehouse_daily",
    default_args=default_args,
    description=f"Bronze ingest → Cosmos dbt ({DBT_TARGET}) → GE quality gate",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "platform", "cosmos", DBT_TARGET],
) as dag:
    start = EmptyOperator(task_id="start")

    ingest_bronze = BashOperator(
        task_id="ingest_bronze",
        bash_command=f"{ENV_EXPORTS} && python {REPO_ROOT / 'ingestion' / 'run_ingest.py'}",
    )

    if DBT_TARGET == "iceberg":
        seed_bronze = BashOperator(
            task_id="seed_bronze",
            bash_command=f"{ENV_EXPORTS} && python {REPO_ROOT / 'ingestion' / 'seed_iceberg_bronze.py'}",
        )
    else:
        seed_bronze = BashOperator(
            task_id="dbt_seed",
            bash_command=f"{ENV_EXPORTS} && cd {DBT_DIR} && dbt seed --target dev",
        )

    dbt_transform = DbtTaskGroup(
        group_id="dbt_transform",
        project_config=project_config,
        profile_config=profile_config,
        execution_config=execution_config,
        render_config=render_config,
        operator_args={
            "py_requirements": DBT_REQUIREMENTS,
            "install_deps": True,
            "append_env": True,
            "env": operator_env,
        },
    )

    quality_gate = BashOperator(
        task_id="quality_gate",
        bash_command=f"{ENV_EXPORTS} && python {REPO_ROOT / 'quality' / 'run_checkpoint.py'}",
    )

    publish = EmptyOperator(task_id="publish_marts")

    if DBT_TARGET == "iceberg":
        start >> seed_bronze >> ingest_bronze >> dbt_transform >> quality_gate >> publish
    else:
        start >> ingest_bronze >> seed_bronze >> dbt_transform >> quality_gate >> publish
