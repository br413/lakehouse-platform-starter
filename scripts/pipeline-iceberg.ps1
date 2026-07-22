# Run the native Iceberg + Trino pipeline (requires Docker stack)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:DBT_TARGET = "iceberg"
$env:TRINO_HOST = "localhost"
$env:TRINO_PORT = "8090"
$env:ICEBERG_CATALOG_URI = "http://localhost:8181"
$env:ICEBERG_S3_ENDPOINT = "http://localhost:9000"
$env:DBT_PROFILES_DIR = Join-Path $Root "transform\dbt"
$env:AWS_ACCESS_KEY_ID = "admin"
$env:AWS_SECRET_ACCESS_KEY = "password"

python ingestion/seed_iceberg_bronze.py
python ingestion/ingest_events_iceberg.py
Push-Location transform/dbt
dbt deps
dbt build --select staging+ marts+ --target iceberg
Pop-Location
python quality/run_checkpoint.py

Write-Host "Iceberg pipeline complete. Query: SELECT * FROM iceberg.marts.fct_daily_events (Trino :8090)"
