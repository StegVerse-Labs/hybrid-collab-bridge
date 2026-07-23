#!/usr/bin/env python3
"""Validate Human–LLM pair assessment JSONL records.

The validator intentionally avoids score-only admission. Critical failures,
missing comprehension, and incomplete traces take precedence over averages.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_TESTS = {
    "meaning_preservation",
    "vocabulary_alignment",
    "boundary_control",
    "contradiction_detection",
    "evidence_classification",
    "audit_gap_control",
    "review_comprehension",
    "revision_integrity",
    "independent_reconstruction",
}
VALID_OUTCOMES = {"PASS", "PARTIAL", "FAIL", "INDETERMINATE"}
VALID_ATTRIBUTIONS = {
    "human_originated",
    "model_originated",
    "interaction_originated",
    "review_failed",
    "translation_originated",
    "boundary_originated",
    "amplification_originated",
}
HIGH_CONSEQUENCE = {"high", "critical"}


def recommended_outcome(record: dict[str, Any]) -> str:
    tests = record["tests"]
    statuses = [test["status"] for test in tests.values()]

    if any(test["critical"] and test["status"] == "FAIL" for test in tests.values()):
        return "FAIL"
    if any(test["critical"] and test["status"] == "INDETERMINATE" for test in tests.values()):
        return "INDETERMINATE"

    review = record["review"]
    if record.get("claim_consequence") in HIGH_CONSEQUENCE and not review["comprehension_demonstrated"]:
        return "FAIL"

    if "INDETERMINATE" in statuses:
        return "INDETERMINATE"
    if "FAIL" in statuses or "PARTIAL" in statuses:
        return "PARTIAL"
    return "PASS"


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"assessment_id", "trace_id", "timestamp", "tests", "review", "overall_outcome", "error_attribution"}
    missing = sorted(required - record.keys())
    if missing:
        return [f"missing required fields: {', '.join(missing)}"]

    tests = record.get("tests")
    if not isinstance(tests, dict):
        return ["tests must be an object"]
    missing_tests = sorted(REQUIRED_TESTS - tests.keys())
    extra_tests = sorted(tests.keys() - REQUIRED_TESTS)
    if missing_tests:
        errors.append(f"missing tests: {', '.join(missing_tests)}")
    if extra_tests:
        errors.append(f"unknown tests: {', '.join(extra_tests)}")

    for name, result in tests.items():
        if not isinstance(result, dict):
            errors.append(f"{name}: result must be an object")
            continue
        for field in ("status", "score", "critical", "evidence"):
            if field not in result:
                errors.append(f"{name}: missing {field}")
        if result.get("status") not in VALID_OUTCOMES:
            errors.append(f"{name}: invalid status")
        score = result.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
            errors.append(f"{name}: score must be between 0 and 1")
        if not isinstance(result.get("critical"), bool):
            errors.append(f"{name}: critical must be boolean")
        evidence = result.get("evidence")
        if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
            errors.append(f"{name}: evidence must be a string array")

    review = record.get("review")
    if not isinstance(review, dict):
        errors.append("review must be an object")
    else:
        for field in ("human_present", "comprehension_demonstrated", "objections_considered"):
            if not isinstance(review.get(field), bool):
                errors.append(f"review.{field} must be boolean")

    outcome = record.get("overall_outcome")
    if outcome not in VALID_OUTCOMES:
        errors.append("invalid overall_outcome")

    attributions = record.get("error_attribution")
    if not isinstance(attributions, list):
        errors.append("error_attribution must be an array")
    else:
        invalid = sorted(set(attributions) - VALID_ATTRIBUTIONS)
        if invalid:
            errors.append(f"invalid error attribution: {', '.join(invalid)}")

    if not errors:
        expected = recommended_outcome(record)
        if outcome != expected:
            errors.append(f"overall_outcome must be {expected}, got {outcome}")
    return errors


def validate_jsonl(path: Path) -> int:
    failures = 0
    records = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            records += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                failures += 1
                print(f"{path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                continue
            errors = validate_record(record)
            if errors:
                failures += 1
                for error in errors:
                    print(f"{path}:{line_number}: {error}", file=sys.stderr)

    if records == 0:
        print(f"{path}: no records found", file=sys.stderr)
        return 1
    if failures:
        print(f"FAIL: {failures}/{records} records invalid", file=sys.stderr)
        return 1
    print(f"PASS: {records} records valid")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="JSONL assessment file")
    args = parser.parse_args()
    return validate_jsonl(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
