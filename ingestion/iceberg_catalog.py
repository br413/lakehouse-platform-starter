"""Shared helpers for Iceberg REST catalog access."""

from __future__ import annotations

import os
from functools import lru_cache

from pyiceberg.catalog import load_catalog


def catalog_properties() -> dict[str, str]:
    uri = os.environ.get("ICEBERG_CATALOG_URI", "http://localhost:8181")
    s3_endpoint = os.environ.get("ICEBERG_S3_ENDPOINT", "http://localhost:9000")
    return {
        "uri": uri,
        "warehouse": os.environ.get("ICEBERG_WAREHOUSE", "s3://warehouse/"),
        "s3.endpoint": s3_endpoint,
        "s3.access-key-id": os.environ.get("AWS_ACCESS_KEY_ID", "admin"),
        "s3.secret-access-key": os.environ.get("AWS_SECRET_ACCESS_KEY", "password"),
        "s3.path-style-access": "true",
        "s3.region": os.environ.get("AWS_REGION", "us-east-1"),
    }


@lru_cache(maxsize=1)
def get_catalog():
    return load_catalog("rest", **catalog_properties())
