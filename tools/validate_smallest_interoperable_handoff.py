#!/usr/bin/env python3
"""Validate the smallest interoperable handoff contract without external dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "handoff_id",
    "originating_layer",
    "intent",
    "evidence_references",
    "reasoning_summary",
    "uncertainty",
    "unresolved_dependencies",
    "provenance",
    "withheld_claims",
}
WITHHELD_FIELDS = {
    "consent",
    "authority",
    "admissibility",
    "commitment",
    "execution_status",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be a JSON object"]

    missing = REQUIRED_TOP_LEVEL - record.keys()
    if missing:
        errors.append(f"missing required fields: {', '.join(sorted(missing))}")

    if record.get("schema_version") != "SIH-v1":
        errors.append("schema_version must equal SIH-v1")

    for field in ("handoff_id", "originating_layer", "intent", "reasoning_summary"):
        if not _nonempty_string(record.get(field)):
            errors.append(f"{field} must be a non-empty string")

    evidence = record.get("evidence_references")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence_references must contain at least one evidence binding")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"evidence_references[{index}] must be an object")
                continue
            if not _nonempty_string(item.get("reference")):
                errors.append(f"evidence_references[{index}].reference is required")
            if not _nonempty_string(item.get("claim_supported")):
                errors.append(f"evidence_references[{index}].claim_supported is required")

    uncertainty = record.get("uncertainty")
    if not isinstance(uncertainty, dict):
        errors.append("uncertainty must be an object")
    else:
        if uncertainty.get("level") not in {"low", "medium", "high", "unknown"}:
            errors.append("uncertainty.level is invalid")
        if not _nonempty_string(uncertainty.get("basis")):
            errors.append("uncertainty.basis is required")

    dependencies = record.get("unresolved_dependencies")
    if not isinstance(dependencies, list):
        errors.append("unresolved_dependencies must be an array")
    elif not dependencies:
        errors.append("at least one unresolved downstream dependency must be preserved")
    elif any(not _nonempty_string(item) for item in dependencies):
        errors.append("every unresolved dependency must be a non-empty string")

    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for field in ("recorded_at", "actor", "source_system"):
            if not _nonempty_string(provenance.get(field)):
                errors.append(f"provenance.{field} is required")

    withheld = record.get("withheld_claims")
    if not isinstance(withheld, dict):
        errors.append("withheld_claims must be an object")
    else:
        missing_withheld = WITHHELD_FIELDS - withheld.keys()
        if missing_withheld:
            errors.append(
                "withheld_claims missing fields: " + ", ".join(sorted(missing_withheld))
            )
        for field in sorted(WITHHELD_FIELDS):
            if withheld.get(field) != "UNRESOLVED":
                errors.append(
                    f"boundary overreach: withheld_claims.{field} must remain UNRESOLVED"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", nargs="+", type=Path)
    parser.add_argument(
        "--expect-invalid",
        action="store_true",
        help="Succeed only when every supplied record is rejected.",
    )
    args = parser.parse_args()

    failed = False
    for path in args.records:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors = [f"unable to read valid JSON: {exc}"]
        else:
            errors = validate(record)

        if args.expect_invalid:
            if errors:
                print(f"EXPECTED_REJECT {path}: {'; '.join(errors)}")
            else:
                print(f"UNEXPECTED_ALLOW {path}")
                failed = True
        elif errors:
            print(f"REJECT {path}: {'; '.join(errors)}")
            failed = True
        else:
            print(f"ALLOW {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
