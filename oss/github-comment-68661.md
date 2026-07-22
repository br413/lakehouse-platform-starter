## Design proposal for RUN-level OpenLineage events on dbt Cloud jobs

Hi @kacpermuda — I'd like to take this on. Below is a concrete plan; happy to adjust before opening a draft PR.

### Problem recap

Today `generate_openlineage_events_from_dbt_cloud_run()` sets:

```python
parent_metadata = _get_parent_run_metadata(task_instance)
processor.dbt_run_metadata = parent_metadata
```

So model/test/source events parent directly to the **Airflow task run**. The dbt Cloud Job Run layer is missing.

### Proposed hierarchy

```
Airflow Task Run
└── dbt Cloud Job Run          ← new RUN-level entity
    ├── dbt Model
    ├── dbt Test
    └── dbt Snapshot
```

### Implementation plan

**Step 1 — START event when job is triggered**

Add `get_openlineage_facets_on_start()` to `DbtCloudRunJobOperator` (or emit via listener hook after `execute()` triggers the run and `self.run_id` is set):

- `namespace`: `dbt-cloud` (or configurable via connection extra?)
- `job.name`: `dbt-cloud-job-{job_id}`
- `run.runId`: `dbt-cloud-run-{run_id}` (native dbt Cloud run ID)
- `parent`: Airflow task run (existing `lineage_run_id(task_instance)`)
- Facets: `account_id`, `project_id`, `environment_id` if available from hook

**Step 2 — Reparent artifact events**

In `generate_openlineage_events_from_dbt_cloud_run()`:

```python
airflow_parent = _get_parent_run_metadata(task_instance)
dbt_cloud_parent = ParentRunMetadata(
    run_id=f"dbt-cloud-run-{operator.run_id}",
    job_name=f"dbt-cloud-job-{operator.job_id}",
    job_namespace="dbt-cloud",
    root_parent_run_id=airflow_parent.run_id,
    root_parent_job_name=airflow_parent.job_name,
    root_parent_job_namespace=airflow_parent.job_namespace,
)
processor.dbt_run_metadata = dbt_cloud_parent
```

**Step 3 — COMPLETE/FAIL on termination**

When the poll loop in `execute()` sees terminal status (`success` / `error` / `cancelled`), emit terminal event for the dbt Cloud job run before/after child artifact processing.

**Step 4 — Tests**

- Mock `DbtCloudHook.get_job_run()` + artifact responses
- Assert emitted event order: START (dbt Cloud job) → child model events with correct parent → COMPLETE/FAIL
- Regression: `wait_for_termination=False` still skips child events (existing behavior)

### Open questions

1. **Namespace naming** — is `dbt-cloud` acceptable, or should we derive from connection/host (e.g. `https://cloud.getdbt.com`)?
2. **Cross-repo work** — you noted this may extend beyond Airflow into `openlineage-python` dbt integration. Should the RUN-level START/COMPLETE live entirely in Airflow adapter, or do we need a `DbtCloudArtifactProcessor` change upstream?
3. **Sensor path** — `DbtCloudJobRunSensor` also calls `generate_openlineage_events_from_dbt_cloud_run()`. Same treatment?

I'll start with a draft PR focused on Steps 1–3 in the dbt Cloud provider this week. Let me know if you'd prefer a smaller initial slice (e.g. START + reparenting only, terminal event follow-up).
