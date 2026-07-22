.PHONY: up down pipeline pipeline-iceberg seed transform test quality docs lint clean

PYTHON ?= python
DBT_DIR := transform/dbt
DUCKDB_PATH := storage/warehouse/dev.duckdb
export DUCKDB_PATH
export DBT_PROFILES_DIR := $(CURDIR)/$(DBT_DIR)

up:
	docker compose up -d

down:
	docker compose down

deps:
	cd $(DBT_DIR) && dbt deps

seed: deps
	cd $(DBT_DIR) && dbt seed --target dev

ingest:
	$(PYTHON) ingestion/run_ingest.py

transform: deps
	cd $(DBT_DIR) && dbt build --select staging+ marts+ --target dev

pipeline: ingest seed transform quality

# Native Iceberg path (requires docker compose up — Trino on :8090)
pipeline-iceberg: deps
	$(PYTHON) ingestion/seed_iceberg_bronze.py
	$(PYTHON) ingestion/ingest_events_iceberg.py
	cd $(DBT_DIR) && DBT_TARGET=iceberg dbt build --select staging+ marts+ --target iceberg
	DBT_TARGET=iceberg $(PYTHON) quality/run_checkpoint.py

quality:
	$(PYTHON) quality/run_checkpoint.py

test:
	python -m unittest tests.test_pipeline -v

docs: deps
	cd $(DBT_DIR) && dbt seed --target dev && dbt docs generate --target dev

lint:
	cd $(DBT_DIR) && dbt compile --target dev
	cd $(DBT_DIR) && dbt parse --target iceberg
	$(PYTHON) -m py_compile orchestration/airflow/dags/lakehouse_daily.py

clean:
	rm -f $(DUCKDB_PATH)
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages
