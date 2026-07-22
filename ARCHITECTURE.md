# Architecture

## Stack

| Layer | Tool | Role |
|-------|------|------|
| Ingestion | Meltano | EL from APIs/files into bronze |
| Storage | Apache Iceberg | Open table format, time travel, multi-engine |
| Transform | dbt | SQL transformations, tests, docs |
| Orchestration | Apache Airflow | Schedule, retry, observe — not transform |
| Lineage | OpenLineage + Marquez | Parent/child run semantics across tools |
| Quality | Great Expectations | Gate mart publish on validation |
| Observability | OpenTelemetry | Distributed traces on pipeline steps |
| Infra | Terraform + Helm | Reproducible environments |

## Data flow

1. **Bronze** — raw events land in Iceberg (`bronze.events`) partitioned by `event_date`.
2. **Silver** — dbt staging models clean types, dedupe, apply business keys.
3. **Gold** — dbt marts (`fct_*`, `dim_*`) power analytics and downstream apps.
4. **Quality** — GE checkpoint runs after dbt; failure blocks downstream DAG tasks.
5. **Lineage** — Airflow emits OL events; dbt Cloud job runs are RUN-level parents (see ADR-003).

## Orchestration boundaries

**In DAGs (wiring only):**
- Task dependencies, retries, pools, SLAs
- Trigger dbt via Cosmos TaskGroup or dbt Cloud operator
- Pass conn_ids and partition macros

**Not in DAGs:**
- Business logic SQL
- Column-level transforms
- Ad-hoc Python ETL (use dbt Python models or Spark instead)

## Environments

| Env | Purpose | Notes |
|-----|---------|-------|
| `dev` | Local docker-compose | Fake data, full stack |
| `staging` | Pre-prod validation | Mirrors prod schema |
| `prod` | Production | `max_active_runs=1` on marts DAG |

## Related ADRs

- [001 — Iceberg over Delta](./docs/decisions/001-iceberg-over-delta.md)
- [002 — Thin orchestration](./docs/decisions/002-thin-orchestration.md)
- [003 — OpenLineage as contract](./docs/decisions/003-openlineage-as-contract.md)
