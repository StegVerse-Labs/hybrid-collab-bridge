from __future__ import annotations
import hashlib
import json


def digest_object(obj: dict) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
