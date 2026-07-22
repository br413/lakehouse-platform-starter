"""Daily lakehouse pipeline: ingest → transform → quality gate."""

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

ENV_EXPORTS = (
    f"export DUCKDB_PATH={DUCKDB_PATH} "
    f"&& export DBT_PROFILES_DIR={DBT_DIR} "
    f"&& export ICEBERG_CATALOG_URI={os.environ.get('ICEBERG_CATALOG_URI', '')} "
    f"&& export ICEBERG_S3_ENDPOINT={os.environ.get('ICEBERG_S3_ENDPOINT', '')} "
)

profile_config = ProfileConfig(
    profile_name="lakehouse_platform",
    target_name="dev",
    profiles_yml_filepath=DBT_DIR / "profiles.yml",
)

project_config = ProjectConfig(
    dbt_project_path=str(DBT_DIR),
    env_vars={"DUCKDB_PATH": str(DUCKDB_PATH)},
)

execution_config = ExecutionConfig(
    execution_mode=ExecutionMode.VIRTUALENV,
    virtualenv_dir=str(REPO_ROOT / ".dbt_venv"),
)

render_config = RenderConfig(
    select=["path:models/staging", "path:models/intermediate", "path:models/marts"],
    test_behavior=TestBehavior.BUILD,
)

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
    description="Bronze ingest → Cosmos dbt transform → GE quality gate",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "platform", "cosmos"],
) as dag:
    start = EmptyOperator(task_id="start")

    ingest_bronze = BashOperator(
        task_id="ingest_bronze",
        bash_command=f"{ENV_EXPORTS} && python {REPO_ROOT / 'ingestion' / 'run_ingest.py'}",
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"{ENV_EXPORTS} && cd {DBT_DIR} && dbt seed",
    )

    dbt_transform = DbtTaskGroup(
        group_id="dbt_transform",
        project_config=project_config,
        profile_config=profile_config,
        execution_config=execution_config,
        render_config=render_config,
        operator_args={
            "py_requirements": ["dbt-duckdb>=1.9.0"],
            "install_deps": True,
            "append_env": True,
            "env": {
                "DUCKDB_PATH": str(DUCKDB_PATH),
                "DBT_PROFILES_DIR": str(DBT_DIR),
            },
        },
    )

    quality_gate = BashOperator(
        task_id="quality_gate",
        bash_command=f"{ENV_EXPORTS} && python {REPO_ROOT / 'quality' / 'run_checkpoint.py'}",
    )

    publish = EmptyOperator(task_id="publish_marts")

    start >> ingest_bronze >> dbt_seed >> dbt_transform >> quality_gate >> publish
