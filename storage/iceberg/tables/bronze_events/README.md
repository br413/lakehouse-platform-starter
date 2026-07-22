# Iceberg bronze table — `bronze.events`

Partition spec: `event_date` (day)  
Format: Parquet with Iceberg v2 metadata  
Location: `s3://warehouse/bronze/events/` (MinIO in local Docker)

## Local catalog

REST catalog runs at `http://localhost:8181` via `apache/iceberg-rest-fixture`.

PyIceberg config: [catalog/pyiceberg.yaml](../catalog/pyiceberg.yaml)

Initialize namespace + table:

```bash
pip install 'pyiceberg[pyarrow,s3fs]'
export ICEBERG_CATALOG_URI=http://localhost:8181
export ICEBERG_S3_ENDPOINT=http://localhost:9000
python storage/iceberg/scripts/init_catalog.py
```

## Schema

| Column | Type | Notes |
|--------|------|-------|
| id | string | Event identifier |
| event_type | string | page_view, signup, purchase |
| event_timestamp | timestamp | UTC |
| user_id | string | Anonymous user id |
| payload | string | JSON blob |

## Ingest

Docker full stack uses `ingestion/ingest_events_iceberg.py` → sync to DuckDB for dbt.  
Production path: dbt-trino or Spark SQL directly on Iceberg (see ADR-001).
