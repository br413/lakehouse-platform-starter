"""Daily lakehouse pipeline: ingest → transform → quality gate."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator

# Production: replace with Cosmos DbtTaskGroup or DbtCloudRunJobOperator
# from cosmos import DbtTaskGroup

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
    description="Bronze ingest → dbt transform → GE quality gate",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "platform"],
) as dag:
    start = EmptyOperator(task_id="start")

    # TODO: wire Meltano/Airbyte sync → Iceberg bronze
    ingest_bronze = EmptyOperator(task_id="ingest_bronze")

    # TODO: Cosmos TaskGroup or DbtCloudRunJobOperator
    # dbt_transform = DbtTaskGroup(...)
    dbt_transform = EmptyOperator(task_id="dbt_transform")

    # TODO: GreatExpectationsOperator checkpoint
    quality_gate = EmptyOperator(task_id="quality_gate")

    publish = EmptyOperator(task_id="publish_marts")

    start >> ingest_bronze >> dbt_transform >> quality_gate >> publish
