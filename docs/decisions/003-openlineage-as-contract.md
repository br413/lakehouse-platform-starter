# ADR 003: OpenLineage as the lineage contract

## Status

Accepted

## Context

Lineage must be queryable across orchestrator (Airflow), transform (dbt Cloud), and storage (warehouse/Iceberg).

## Decision

Standardize on **OpenLineage** with Marquez (or DataHub) as the backend. Enforce correct parent/child hierarchy:

```
Airflow Task Run
└── dbt Cloud Job Run    ← RUN-level parent (apache/airflow#68661)
    ├── dbt Model
    ├── dbt Test
    └── dbt Snapshot
```

## Rationale

- OpenLineage is the de facto standard (Airflow AIP-53, dbt integration)
- Wrong hierarchy breaks impact analysis and audit trails
- Contrib target: fix dbt Cloud RUN-level events in Airflow upstream

## Consequences

- `OPENLINEAGE` env/config required on all Airflow deployments
- dbt Cloud operator must emit START/COMPLETE for job runs before child events
- Reference implementation documented in this repo's Airflow config

## Implementation notes (for #68661)

Current code in `providers/dbt/cloud/utils/openlineage.py` sets:

```python
parent_metadata = _get_parent_run_metadata(task_instance)  # → Airflow task
processor.dbt_run_metadata = parent_metadata
```

Target state:

1. Emit OL START when dbt Cloud run is triggered (`run_id` from API)
2. Build `ParentRunMetadata` pointing at dbt Cloud job run UUID
3. Pass that as parent to `DbtCloudArtifactProcessor`
4. Emit COMPLETE/FAIL when poll loop sees terminal status
