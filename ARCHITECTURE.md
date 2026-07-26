# Architecture

> **See also:** [README](./README.md) (quick start) · [Interview walkthrough](./docs/interview-walkthrough.md) (demo script) · [ADRs](./docs/decisions/)

## Stack

| Layer | Tool | Role |
|-------|------|------|
| Ingestion | PyIceberg | Bronze writes to Iceberg on MinIO/S3 (Meltano planned) |
| Storage | Apache Iceberg | Open table format, time travel, multi-engine |
| Query | Trino | Federated SQL over Iceberg (Docker demo) |
| Transform | dbt (duckdb / trino) | SQL transformations, tests, docs |
| Orchestration | Apache Airflow + Cosmos | Schedule, retry, observe — not transform |
| Lineage | OpenLineage + Marquez | Parent/child run semantics across tools |
| Quality | Great Expectations | Gate mart publish on validation |
| Infra | Terraform | Bronze S3 bucket + IAM (Helm/K8s planned) |

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

## Environment variables

Canonical names used across Makefile, scripts, DAG, and CI:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DBT_TARGET` | `dev` | Transform backend: `dev` (DuckDB) or `iceberg` (Trino) |
| `DUCKDB_PATH` | `storage/warehouse/dev.duckdb` | DuckDB warehouse file (dev target) |
| `DBT_PROFILES_DIR` | `transform/dbt` | dbt profiles location |
| `ICEBERG_CATALOG_URI` | — | Iceberg REST catalog URL (Docker: `http://localhost:8181`) |
| `ICEBERG_S3_ENDPOINT` | — | S3-compatible endpoint (Docker: `http://localhost:9000`) |
| `TRINO_HOST` / `TRINO_PORT` | — | Trino connection (Docker host: `8090`) |

`DBT_TARGET=iceberg` is set in `docker-compose.yml` for the Airflow stack. Local fast path leaves it at `dev`.

## Targets and environments

| Target / env | Engine | When to use |
|--------------|--------|-------------|
| `dev` (dbt) | DuckDB | CI, local smoke test, no Docker (~30s) |
| `iceberg` (dbt) | Trino + Iceberg | Docker demo, native lakehouse path |
| `staging` / `prod` | — | Planned — schema mirrors prod; `max_active_runs=1` on marts DAG |

## Related ADRs

- [001 — Iceberg over Delta](./docs/decisions/001-iceberg-over-delta.md)
- [002 — Thin orchestration](./docs/decisions/002-thin-orchestration.md)
- [003 — OpenLineage as contract](./docs/decisions/003-openlineage-as-contract.md)
