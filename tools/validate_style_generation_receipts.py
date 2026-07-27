#!/usr/bin/env python3
"""Validate governed style-generation receipts and fail closed on provenance inflation."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/style_generation_receipt.schema.json"


def canonical_payload(record: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in record.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate(record: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema
        jsonschema.validate(record, schema, format_checker=jsonschema.FormatChecker())
    except ImportError:
        errors.append("jsonschema dependency missing")
        return errors
    except jsonschema.ValidationError as exc:
        errors.append(f"schema: {exc.message}")
        return errors

    revision = record["human_revision"]
    if revision["applied"] and not revision["revision_hash"]:
        errors.append("human revision requires revision_hash")
    if not revision["applied"] and revision["revision_hash"] is not None:
        errors.append("unapplied human revision must have null revision_hash")

    signature = record["signature"]
    level = record["provenance_level"]
    if level == "cryptographically_bound":
        if signature["algorithm"] != "hmac-sha256":
            errors.append("current validator supports cryptographically_bound only with hmac-sha256")
        else:
            key = os.getenv("HCB_STYLE_RECEIPT_KEY")
            if not key:
                errors.append("HCB_STYLE_RECEIPT_KEY is required for cryptographic verification")
            else:
                expected = hmac.new(key.encode(), canonical_payload(record), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected, signature["value"]):
                    errors.append("signature verification failed")
    elif signature["algorithm"] != "none" or signature["value"]:
        errors.append("non-cryptographic provenance cannot carry a signature claim")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate_style_generation_receipts.py FILE [FILE ...]", file=sys.stderr)
        return 2
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    failed = False
    for raw in argv[1:]:
        path = Path(raw)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("receipt must be a JSON object")
            problems = validate(data, schema)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            problems = [str(exc)]
        if problems:
            failed = True
            print(f"FAIL {path}")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
