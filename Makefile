.PHONY: help up down deps seed ingest transform pipeline pipeline-iceberg quality test docs lint clean

PYTHON ?= python
DBT_DIR := transform/dbt
DUCKDB_PATH := storage/warehouse/dev.duckdb
export DUCKDB_PATH
export DBT_PROFILES_DIR := $(CURDIR)/$(DBT_DIR)

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

up: ## Start Docker stack (Airflow, Trino, Iceberg, Marquez)
	docker compose up -d

down: ## Stop Docker stack
	docker compose down

deps: ## Install dbt package dependencies
	cd $(DBT_DIR) && dbt deps

seed: deps ## Load dbt seed data (dev target)
	cd $(DBT_DIR) && dbt seed --target dev

ingest: ## Bronze ingest (routes via DBT_TARGET)
	$(PYTHON) ingestion/run_ingest.py

transform: deps ## dbt build staging + marts (dev target)
	cd $(DBT_DIR) && dbt build --select staging+ marts+ --target dev

pipeline: ingest seed transform quality ## Full DuckDB path: ingest → dbt → GE

pipeline-iceberg: deps ## Iceberg path (requires docker compose up)
	$(PYTHON) ingestion/seed_iceberg_bronze.py
	$(PYTHON) ingestion/ingest_events_iceberg.py
	cd $(DBT_DIR) && DBT_TARGET=iceberg dbt build --select staging+ marts+ --target iceberg
	DBT_TARGET=iceberg $(PYTHON) quality/run_checkpoint.py

quality: ## Great Expectations checkpoint on mart
	$(PYTHON) quality/run_checkpoint.py

test: ## End-to-end pipeline smoke test
	python -m unittest tests.test_pipeline -v

docs: deps ## Generate local dbt docs (dev target)
	cd $(DBT_DIR) && dbt seed --target dev && dbt docs generate --target dev

lint: ## Compile dbt + parse DAG
	cd $(DBT_DIR) && dbt compile --target dev
	cd $(DBT_DIR) && dbt parse --target iceberg
	$(PYTHON) -m py_compile orchestration/airflow/dags/lakehouse_daily.py

clean: ## Remove generated warehouse and dbt artifacts
	rm -f $(DUCKDB_PATH)
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages
