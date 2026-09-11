# Quick start

Go from clone → validated mart rows in under a minute. **No Docker required.**

```bash
git clone https://github.com/br413/lakehouse-platform-starter.git
cd lakehouse-platform-starter
pip install -r requirements.txt
make pipeline          # macOS / Linux
# Windows:
.\scripts\demo.ps1
```

## Success looks like

- dbt build passes (staging → int → marts)
- Great Expectations checkpoint passes
- `main_marts.fct_daily_events` has rows in `storage/warehouse/dev.duckdb`

`.\scripts\demo.ps1` prints `MART_ROWS=<n>` plus a short sample and exits non-zero if the mart is empty.

## Next steps

| Goal | Command / link |
|------|----------------|
| Smoke test | `python -m unittest tests.test_pipeline -v` |
| Full lakehouse (Trino + Iceberg + Airflow) | README → Quick start → Full lakehouse |
| Interview rehearsal | [interview-walkthrough.md](./interview-walkthrough.md) |
| Hosted dbt docs | https://br413.github.io/lakehouse-platform-starter/ |
