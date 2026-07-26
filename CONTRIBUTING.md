# Contributing

Thanks for your interest in this project. This repo is primarily a **portfolio reference architecture**, but issues and PRs that improve clarity, correctness, or demo reliability are welcome.

## Getting started

1. Fork and clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the smoke test: `make test` (or `python -m unittest tests.test_pipeline -v`)
4. Run lint: `make lint`

See [ARCHITECTURE.md](./ARCHITECTURE.md#environment-variables) for canonical env var names (`DBT_TARGET`, `DUCKDB_PATH`, `DBT_PROFILES_DIR`).

## Pull request guidelines

- Keep changes focused — one concern per PR
- Ensure CI passes (`dbt build`, smoke test, DAG parse, `terraform validate`)
- Match existing code style and documentation tone
- Update README or ADRs if you change architecture or behavior

## Development paths

| Path | Command |
|------|---------|
| DuckDB (fast) | `make pipeline` |
| Iceberg + Trino (Docker) | `docker compose up -d && make pipeline-iceberg` |
| dbt docs locally | `make docs` |
| Windows (no make) | `.\scripts\pipeline.ps1` |

Run `make help` for all Makefile targets.

## Reporting issues

Include:

- Steps to reproduce
- Expected vs actual behavior
- OS and Python version
- Relevant logs (dbt, Airflow, or Docker)

## Code of conduct

Be respectful and constructive. This project follows standard open-source community norms.
