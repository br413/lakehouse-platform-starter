# Run the full local pipeline (Windows / PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:DUCKDB_PATH = Join-Path $Root "storage\warehouse\dev.duckdb"
$env:DBT_PROFILES_DIR = Join-Path $Root "transform\dbt"

python ingestion/run_ingest.py
Push-Location transform/dbt
dbt deps
dbt seed
dbt build --select staging+ marts+
Pop-Location
python quality/run_checkpoint.py

Write-Host "Pipeline complete. Mart rows in $env:DUCKDB_PATH"
