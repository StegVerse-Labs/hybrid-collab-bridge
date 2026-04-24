from __future__ import annotations
from typing import Dict, Any
from .hashing import digest_object


def ingest_object(obj: dict, source: str = "unknown") -> dict:
    result = {
        "ingested": True,
        "source": source,
        "payload": obj,
        "payload_hash": digest_object(obj),
        "schema_valid": True,
    }
    return result
