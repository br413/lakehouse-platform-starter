# ADR 001: Iceberg over Delta for the lakehouse storage layer

## Status

Accepted

## Context

We need an open table format for bronze/silver layers with ACID semantics, time travel, and multi-engine reads (Spark, Trino, DuckDB).

## Decision

Use **Apache Iceberg** with a REST catalog.

## Rationale

- Neutral ASF project; not vendor-tied like Delta on Databricks-only paths
- Strong REST catalog ecosystem (PyIceberg, Airflow Iceberg provider)
- Active Airflow provider development (catalog introspection, LLM operators)

## Consequences

- Catalog service required (REST or Glue/Hive metastore)
- Compaction jobs needed for write-heavy tables
- Team learns Iceberg partition specs and snapshot semantics
