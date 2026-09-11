# Demo the DuckDB lakehouse path (Windows / PowerShell)
# Usage: .\scripts\demo.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "lakehouse-platform-starter demo (DuckDB path, no Docker)" -ForegroundColor Cyan
Write-Host "========================================================="
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python not found on PATH"
}
if (-not (Get-Command dbt -ErrorAction SilentlyContinue)) {
    Write-Host "Installing requirements (includes dbt-duckdb)..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

$env:DUCKDB_PATH = Join-Path $Root "storage\warehouse\dev.duckdb"
$env:DBT_PROFILES_DIR = Join-Path $Root "transform\dbt"

Write-Host "[1/4] Bronze ingest..." -ForegroundColor Green
python ingestion/run_ingest.py
if ($LASTEXITCODE -ne 0) { throw "ingest failed" }

Write-Host "[2/4] dbt deps + seed + build..." -ForegroundColor Green
Push-Location transform/dbt
try {
    dbt deps
    if ($LASTEXITCODE -ne 0) { throw "dbt deps failed" }
    dbt seed --target dev
    if ($LASTEXITCODE -ne 0) { throw "dbt seed failed" }
    dbt build --select staging+ marts+ --target dev
    if ($LASTEXITCODE -ne 0) { throw "dbt build failed" }
}
finally {
    Pop-Location
}

Write-Host "[3/4] Great Expectations quality gate..." -ForegroundColor Green
python quality/run_checkpoint.py
if ($LASTEXITCODE -ne 0) { throw "quality gate failed" }

Write-Host "[4/4] Verify mart rows..." -ForegroundColor Green
python scripts/verify_mart.py
if ($LASTEXITCODE -ne 0) { throw "mart verification failed" }

Write-Host ""
Write-Host "Demo OK" -ForegroundColor Cyan
Write-Host "  Warehouse: $env:DUCKDB_PATH"
Write-Host "  Next: python -m unittest tests.test_pipeline -v"
Write-Host "  Docs:  https://br413.github.io/lakehouse-platform-starter/"
Write-Host ""
