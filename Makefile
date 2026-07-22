.PHONY: up down pipeline seed transform test quality docs lint clean

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
	cd $(DBT_DIR) && dbt seed

ingest:
	$(PYTHON) ingestion/run_ingest.py

transform: deps
	cd $(DBT_DIR) && dbt build --select staging+ marts+

pipeline: ingest seed transform quality

quality:
	$(PYTHON) quality/run_checkpoint.py

test:
	python -m unittest tests.test_pipeline -v

docs: deps
	cd $(DBT_DIR) && dbt docs generate

lint:
	cd $(DBT_DIR) && dbt compile
	$(PYTHON) -m py_compile orchestration/airflow/dags/*.py

clean:
	rm -f $(DUCKDB_PATH)
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages
