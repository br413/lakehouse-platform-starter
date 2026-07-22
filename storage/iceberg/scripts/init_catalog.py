#!/usr/bin/env python3
"""Initialize Iceberg REST catalog namespace and bronze.events table."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from pyiceberg.schema import Schema  # noqa: E402
from pyiceberg.types import NestedField, StringType, TimestampType  # noqa: E402

from ingestion.iceberg_catalog import get_catalog  # noqa: E402

TABLE = ("bronze", "events")
SCHEMA = Schema(
    NestedField(1, "id", StringType(), required=True),
    NestedField(2, "event_type", StringType(), required=True),
    NestedField(3, "event_timestamp", TimestampType(), required=True),
    NestedField(4, "user_id", StringType(), required=True),
    NestedField(5, "payload", StringType(), required=False),
)


def main() -> None:
    catalog = get_catalog()
    namespace = TABLE[0]
    identifier = ".".join(TABLE)
    namespaces = {ns[0] for ns in catalog.list_namespaces()}

    if namespace not in namespaces:
        catalog.create_namespace(namespace)
        print(f"Created namespace: {namespace}")

    if not catalog.table_exists(TABLE):
        catalog.create_table(
            identifier=TABLE,
            schema=SCHEMA,
            properties={"write.format.default": "parquet"},
        )
        print(f"Created table: {identifier}")
    else:
        print(f"Table already exists: {identifier}")


if __name__ == "__main__":
    main()
