#!/usr/bin/env python3
"""Deterministically validate style-attribution observations."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_CAUSES = {
    "model_conditioned_style",
    "prompt_pattern",
    "platform_convention",
    "human_revision",
    "interactional_accommodation",
    "shared_training_or_corpus",
    "unknown",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("record must be a JSON object")
    return data


def validate(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "observation_id",
        "trace_id",
        "artifact_refs",
        "observed_features",
        "candidate_causes",
        "accommodation",
        "attribution_claim",
        "evidence_limits",
        "admissibility",
    ):
        if key not in record:
            errors.append(f"missing required field: {key}")

    if errors:
        return errors

    claim = record["attribution_claim"]
    admissibility = record["admissibility"]
    level = claim.get("level")
    basis = claim.get("basis") or []
    reason_codes = set(admissibility.get("reason_codes") or [])

    if level == "verified" and "verified_provenance_present" not in reason_codes:
        errors.append("verified attribution requires verified_provenance_present")
    if level in {"probabilistic", "verified"} and len(basis) < 2:
        errors.append("probabilistic or verified attribution requires at least two basis items")

    for cause in record.get("candidate_causes", []):
        if cause.get("cause") not in ALLOWED_CAUSES:
            errors.append(f"unsupported cause: {cause.get('cause')}")
        confidence = cause.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append("cause confidence must be between 0 and 1")

    accommodation = record.get("accommodation", {})
    if accommodation.get("asserted") and not accommodation.get("evidence_refs"):
        errors.append("asserted accommodation requires evidence_refs")
    if not accommodation.get("asserted") and accommodation.get("direction") not in {"none", "indeterminate"}:
        errors.append("non-asserted accommodation direction must be none or indeterminate")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate_style_attribution_observations.py FILE [FILE ...]", file=sys.stderr)
        return 2

    failed = False
    for raw in argv[1:]:
        path = Path(raw)
        try:
            errors = validate(load_json(path))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors = [str(exc)]
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
