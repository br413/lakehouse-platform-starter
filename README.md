<div align="center">

# lakehouse-platform-starter

**Production-grade lakehouse reference architecture — runnable, tested, and interview-ready**

[![CI](https://github.com/br413/lakehouse-platform-starter/actions/workflows/ci.yml/badge.svg)](https://github.com/br413/lakehouse-platform-starter/actions/workflows/ci.yml)
[![dbt docs](https://github.com/br413/lakehouse-platform-starter/actions/workflows/docs.yml/badge.svg)](https://github.com/br413/lakehouse-platform-starter/actions/workflows/docs.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-transformations-FF694B?logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![Airflow](https://img.shields.io/badge/Airflow-3.1-017CEE?logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![Iceberg](https://img.shields.io/badge/Apache-Iceberg-0078D4)](https://iceberg.apache.org/)
[![Trino](https://img.shields.io/badge/Trino-SQL-DD00A1)](https://trino.io/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-844FBA?logo=terraform&logoColor=white)](https://www.terraform.io/)

[**Live dbt docs**](https://br413.github.io/lakehouse-platform-starter/) · [**Interview walkthrough**](docs/interview-walkthrough.md) · [**Portfolio**](https://br413.github.io/) · [**Open Airflow PR #70185**](https://github.com/apache/airflow/pull/70185)

<img src="docs/assets/social-preview.svg" alt="lakehouse-platform-starter architecture banner" width="920"/>

</div>

---

**Airflow + Cosmos** → **dbt** → **Iceberg** → **OpenLineage** → **Great Expectations**

Thin orchestration, observable pipelines, incremental marts, and backfill-safe design — built to demonstrate senior data engineering execution, not slide-deck architecture.

## Table of contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Implementation status](#implementation-status)
- [OSS contributions](#oss-contributions)
- [Repo layout](#repo-layout)
- [Documentation](#documentation)

## Highlights

| | |
|---|---|
| **Two runnable paths** | DuckDB for fast CI/local · Trino + Iceberg for credible lakehouse demo |
| **Cosmos orchestration** | Per-model Airflow tasks with virtualenv isolation |
| **14 dbt tests** | Schema, singular, and incremental mart with partition keys |
| **Quality gate** | Great Expectations blocks publish on mart validation failure |
| **Full local stack** | MinIO · Iceberg REST · Trino · Airflow · Marquez in Docker Compose |
| **IaC + CI** | Terraform bronze module · GitHub Actions · hosted dbt docs |

## Architecture

```mermaid
flowchart LR
    subgraph ingest [Ingestion]
        A[PyIceberg ingest] --> B[Iceberg bronze.events]
    end
    subgraph transform [Transform]
        B --> T[Trino]
        T --> C[Cosmos dbt TaskGroup]
        B -.->|dev/CI| C2[DuckDB fast path]
    end
    subgraph orchestrate [Orchestration]
        D[Airflow DAG] --> A
        D --> C
        D --> E[Quality gate]
    end
    subgraph observe [Observability]
        D --> F[OpenLineage → Marquez]
        E --> H[Great Expectations]
    end
    C --> I[fct_daily_events mart]
```

### Design principles

1. **Thin orchestration** — Airflow schedules and observes; dbt owns transform logic.
2. **OpenLineage as contract** — every task emits lineage; dbt Cloud jobs are first-class RUN parents.
3. **Backfill safety** — idempotent DAGs, partition keys, incremental marts, documented runbooks.

See [ARCHITECTURE.md](./ARCHITECTURE.md) and [docs/decisions/](./docs/decisions/).

## Quick start

### Fast path — no Docker (~30 seconds)

```bash
pip install -r requirements.txt
make pipeline          # Linux/macOS
# .\scripts\pipeline.ps1   # Windows
```

Bronze ingest → dbt seed/build → Great Expectations → populated `fct_daily_events` mart.

### Full lakehouse stack — Docker

```bash
docker compose up -d
```

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | admin / admin |
| Marquez (lineage) | http://localhost:5000 | — |
| Trino | http://localhost:8090 | — |
| MinIO console | http://localhost:9001 | admin / password |
| Iceberg REST | http://localhost:8181 | — |

Trigger DAG **`lakehouse_daily`** — uses `DBT_TARGET=iceberg` (PyIceberg → Trino → dbt-trino → Iceberg marts).

```bash
make pipeline-iceberg   # or .\scripts\pipeline-iceberg.ps1
```

### Interview prep

Rehearse from **[docs/interview-walkthrough.md](./docs/interview-walkthrough.md)** — 30-second pitch, demo script, Q&A, and trade-offs.

## Implementation status

| Component | Status | Notes |
|-----------|--------|-------|
| dbt transform (staging → int → marts) | ✅ | Tests, docs site, incremental mart |
| Local pipeline (ingest → dbt → GE) | ✅ | `make pipeline` |
| Iceberg REST + MinIO | ✅ | Docker Compose; PyIceberg ingest |
| dbt-trino on Iceberg | ✅ | Native path via Trino `:8090` |
| Airflow + Cosmos DbtTaskGroup | ✅ | Per-model tasks; virtualenv execution |
| OpenLineage + Marquez | ✅ | Docker Compose |
| Great Expectations gate | ✅ | Blocks publish on failure |
| CI + GitHub Pages dbt docs | ✅ | [Hosted docs](https://br413.github.io/lakehouse-platform-starter/) |
| Terraform (S3 + IAM) | ✅ | Bronze bucket module |
| Interview walkthrough | ✅ | [docs/interview-walkthrough.md](./docs/interview-walkthrough.md) |
| Meltano ingestion | 🔜 | PyIceberg simulates bronze today |
| OpenTelemetry traces | 🔜 | Lineage via Marquez only |
| Helm / K8s deploy | 🔜 | See `infra/terraform/` |

## OSS contributions

| Item | Link | Status |
|------|------|--------|
| Flagship issue | [apache/airflow#68661](https://github.com/apache/airflow/issues/68661) | RUN-level OpenLineage for dbt Cloud |
| **Open PR** | [**#70185**](https://github.com/apache/airflow/pull/70185) | dbt Cloud job metadata on OL events |
| Quick win | [#47160](https://github.com/apache/airflow/issues/47160) | Python 3.12 fork() fix |

Playbook: [oss/AIRFLOW_CONTRIBUTIONS.md](./oss/AIRFLOW_CONTRIBUTIONS.md)

## Repo layout

```
infra/          Terraform (S3 bronze bucket + IAM)
orchestration/  Airflow DAGs + Cosmos + OpenLineage
transform/      dbt project (staging → int → marts)
storage/        Iceberg catalog + Trino config + DuckDB warehouse
quality/        Great Expectations checkpoint
ingestion/      DuckDB + PyIceberg bronze ingest
tests/          End-to-end pipeline smoke test
docs/           ADRs, runbooks, interview walkthrough
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Stack, data flow, env strategy |
| [docs/interview-walkthrough.md](./docs/interview-walkthrough.md) | Interview demo script + Q&A |
| [docs/decisions/](./docs/decisions/) | ADRs (Iceberg, thin orchestration, OpenLineage) |
| [docs/runbooks/backfill-safety.md](./docs/runbooks/backfill-safety.md) | Backfill checklist |
| [dbt docs (hosted)](https://br413.github.io/lakehouse-platform-starter/) | Model lineage + column docs |

---

<div align="center">

**Author:** [Bobby Ray (br413)](https://github.com/br413) · Senior Data Engineer  
**Portfolio:** [br413.github.io](https://br413.github.io/) · **License:** [Apache 2.0](LICENSE)

</div>
