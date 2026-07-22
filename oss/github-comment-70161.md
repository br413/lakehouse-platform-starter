# PR #70161 — reply to @eladkal

Post as a comment on https://github.com/apache/airflow/pull/70161

---

Thanks for the review, @eladkal — fair question.

The first version removed `os.fork()` by calling the lifecycle handlers inline, which dropped the process isolation the fork path provided. I've updated the approach to match what we already do for DAG-run listeners and manual state-change emissions:

1. **Metadata extraction stays in the parent process** (where ORM / task objects are available).
2. **Adapter emission runs via `submit_callable` → `ProcessPoolExecutor` with `forkserver` context**, using a new picklable module-level `_emit_task_instance_event()` (same pattern as `_emit_manual_state_change_event` / `_run_adapter_method`).

This removes the Python 3.12 `DeprecationWarning` without running OL transport code synchronously in the multi-threaded worker/scheduler process, and without sharing the parent's DB connection pool with emission workers.

**Testing:**
- `pytest providers/openlineage/tests/unit/openlineage/plugins/test_listener.py -v`
- `pytest providers/openlineage/tests -k listener -v`
- `prek run --all-files` (or `pre-commit run --all-files`)

Happy to rebase onto latest `main` once this direction looks right.

---

## Updated PR description (optional)

### Problem

On Python 3.12+, the OpenLineage listener emits:

```
DeprecationWarning: This process is multi-threaded, use of fork() may lead to deadlocks in the child.
```

Two sources: `_fork_execute()` calling `os.fork()` for task lifecycle events, and `ProcessPoolExecutor` defaulting to `fork` on Linux.

### Fix

- **Task lifecycle events** (`on_running`, `on_success`, `on_failure`, `on_skipped`): extract metadata in the parent, emit via `submit_callable(_emit_task_instance_event, ...)` instead of `os.fork()`.
- **DAG-run / manual state-change emissions**: use `ProcessPoolExecutor` with `mp_context=multiprocessing.get_context("forkserver")`.
- Remove `_fork_execute`, `_terminate_with_wait`, `_execute`, and related imports.

Closes #47160
