# Iceberg bronze table (local dev placeholder)

Production uses a REST catalog. See ADR-001.

```sql
-- Partition spec: event_date (day)
-- Format: Parquet with Iceberg metadata
-- Location: s3://{bucket}/bronze/events/
```

PyIceberg catalog config example:

```yaml
# storage/iceberg/catalog/.pyiceberg.yaml
catalog:
  local:
    type: rest
    uri: http://localhost:8181/catalog
```
