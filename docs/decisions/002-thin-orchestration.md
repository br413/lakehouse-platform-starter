# ADR 002: Thin orchestration

## Status

Accepted

## Context

Teams often embed transform logic in Airflow PythonOperators, creating untested, opaque pipelines.

## Decision

Airflow **only** schedules, retries, and observes. All transform logic lives in **dbt** (SQL/Python models).

## Rationale

- dbt provides tests, docs, and version control for transforms
- Airflow excels at dependency graphs and operational concerns
- Clear ownership: DE platform owns DAGs; analytics eng owns dbt models

## Consequences

- No business SQL in DAG files
- Cosmos or dbt Cloud operator for dbt invocation
- Lineage spans Airflow task → dbt Cloud job run → dbt resources
