# OSS contribution playbook — Apache Airflow

Lane: **OpenLineage + dbt Cloud** (`providers/openlineage`, `providers/dbt/cloud`)

## Active issues

| Priority | Issue / PR | Action |
|----------|------------|--------|
| Flagship | [#68661](https://github.com/apache/airflow/issues/68661) | RUN-level OL for dbt Cloud — design approved |
| **Active PR** | [**#70185**](https://github.com/apache/airflow/pull/70185) | Attach dbt Cloud job metadata to Airflow OL events |
| Quick win | [#47160](https://github.com/apache/airflow/issues/47160) | Python 3.12 fork() fix — see walkthrough below |
| DX | [#46923](https://github.com/apache/airflow/issues/46923) | Surface dbt Cloud failure logs |
| Stretch | [#70093](https://github.com/apache/airflow/issues/70093) | Deferrable common.ai LLM operators |

## Local dev

```bash
git clone https://github.com/apache/airflow.git
cd airflow
pip install -e "./providers/openlineage[dev]"
pip install -e "./providers/dbt/cloud[dev]"
pytest providers/openlineage/tests -k "not integration"
prek run --from-ref main   # before every push
```

## Public GitHub activity

Do **not** add Cursor/AI attribution footers to issue comments or PR descriptions unless a project explicitly requires it and you choose to comply. Write in your own voice; review and edit all text before posting.

Apache Airflow asks contributors to disclose Gen-AI use in PRs ([guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)). That is a project rule, not a Cursor requirement — follow it only if you agree for that repo.

---

## Walkthrough: Fix #47160 (Python 3.12 fork DeprecationWarning)

**File:** `providers/openlineage/src/airflow/providers/openlineage/plugins/listener.py`

**Symptom:**
```
DeprecationWarning: This process is multi-threaded, use of fork() may lead to deadlocks in the child.
```

### Root cause (two sources)

**Source A — `_fork_execute()` (lines ~985–1024)**

Task lifecycle handlers (`on_running`, `on_success`, `on_failure`, `on_skipped`) call:

```python
self._execute(on_running, "on_running", use_fork=True)
```

Inside `_fork_execute`, the parent process calls `os.fork()` while Airflow's scheduler/worker is **multi-threaded** → Python 3.12 warns.

**Source B — `ProcessPoolExecutor` (lines ~1027–1032)**

DAG-run listeners use a process pool with default Linux `fork` start method — same warning class.

### Fix strategy (from closed PR #67901 — revive and pass CI)

#### Change 1: Eliminate `_fork_execute` for task lifecycle events

Replace fork-with-inline-closure with **picklable module-level function** + existing `submit_callable`:

```python
# NEW module-level function (must be top-level for pickling)
def _emit_task_instance_event(adapter_method, event_type, operator_name, **kwargs):
    redacted_event = adapter_method(**kwargs)
    event_size = len(Serde.to_json(redacted_event).encode("utf-8"))
    Stats.gauge("ol.event.size", event_size, tags={"event_type": event_type, "operator_name": operator_name})
    return redacted_event
```

Then in `on_running()` (and success/failure/skipped), replace:

```python
# BEFORE
self._execute(on_running, "on_running", use_fork=True)

# AFTER — direct call OR submit_callable (PR used submit_callable for isolation)
on_running()  # if emission is fast enough
# OR
self.submit_callable(_emit_task_instance_event, self.adapter.start_task, event_type, operator_name, ...)
```

The closed PR routed through `submit_callable` + `ProcessPoolExecutor` with `forkserver` instead of raw `os.fork()`.

#### Change 2: Use forkserver for ProcessPoolExecutor

```python
@property
def executor(self) -> ProcessPoolExecutor:
    if not self._executor:
        self._executor = ProcessPoolExecutor(
            max_workers=conf.dag_state_change_process_pool_size(),
            initializer=_executor_initializer,
            mp_context=multiprocessing.get_context("forkserver"),  # ADD THIS
        )
    return self._executor
```

`forkserver` starts a clean single-threaded server process; workers fork from it — no warning.

#### Change 3: Delete dead code

Remove `_fork_execute`, `_terminate_with_wait`, `_execute(use_fork=True)` paths, and unused imports (`os`, `psutil`, macOS setproctitle shim) if no longer referenced.

### Why the original PR #67901 closed

Maintainer triage noted:
- Static checks failing → run `prek run --all-files`
- Provider test matrix failures on Python 3.10 + openlineage

**Your job:** Cherry-pick the approach, run full test suite locally, fix any regressions.

### Test commands

```bash
pytest providers/openlineage/tests/unit/plugins/test_listener.py -v
pytest providers/openlineage/tests -k listener -v
prek run --all-files
```

### PR title

```
Fix OpenLineage DeprecationWarning about fork() on Python 3.12+
```

Closes #47160

---

## Walkthrough: Fix #68661 (dbt Cloud RUN-level lineage)

**Files to touch:**
- `providers/dbt/cloud/operators/dbt.py` — add `get_openlineage_facets_on_start`
- `providers/dbt/cloud/utils/openlineage.py` — parent metadata hierarchy
- `providers/openlineage/tests/` — new unit tests

**Current bug** (`openlineage.py` ~line 180):

```python
parent_metadata = _get_parent_run_metadata(task_instance)  # points to Airflow task
processor.dbt_run_metadata = parent_metadata               # dbt models inherit wrong parent
```

**Target:**

```python
# 1. On job trigger — emit START for dbt Cloud job run
adapter.start_task(
    run_id=f"dbt-cloud-run-{operator.run_id}",
    job_name=f"dbt-cloud-job-{operator.job_id}",
    job_namespace="dbt-cloud",
    ...
    parent_run_id=lineage_run_id(task_instance),  # Airflow task is parent
)

# 2. When parsing artifacts — parent is dbt Cloud run, not Airflow task
dbt_cloud_parent = ParentRunMetadata(
    run_id=f"dbt-cloud-run-{operator.run_id}",
    job_name=f"dbt-cloud-job-{operator.job_id}",
    job_namespace="dbt-cloud",
    ...
)
processor.dbt_run_metadata = dbt_cloud_parent

# 3. On terminal status — emit COMPLETE/FAIL for dbt Cloud job run
```

See `docs/decisions/003-openlineage-as-contract.md` in this repo for the hierarchy diagram.
