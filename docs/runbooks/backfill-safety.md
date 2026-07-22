# Backfill safety runbook

## Before backfilling

- [ ] Confirm DAG is **idempotent** for the target date range
- [ ] Set `max_active_runs=1` on marts DAGs
- [ ] Verify partition filter macros (`{{ ds }}`) in all incremental models
- [ ] Notify downstream consumers if marts will be overwritten

## During backfill

- Use `airflow dags backfill` with explicit `--start-date` / `--end-date`
- Monitor OpenLineage in Marquez for unexpected fan-out
- Watch warehouse slot usage (dbt full-refresh is expensive)

## After backfill

- Run GE checkpoint on affected marts
- Compare row counts vs. prior partition snapshots
- Document in #data-platform Slack channel

## Anti-patterns

- Backfilling without `depends_on_past=False` review on incremental models
- Running parallel backfills on the same mart table
- Clearing downstream without clearing upstream (orphan partitions)
