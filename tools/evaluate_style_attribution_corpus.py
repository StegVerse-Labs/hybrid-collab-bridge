#!/usr/bin/env python3
"""Evaluate a governed style-attribution JSONL corpus without inferring model identity."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_CONDITIONS = {
    "model_family",
    "prompt_pattern",
    "platform",
    "human_revision",
    "interactional_accommodation",
}
ALLOWED_CLAIMS = {"none", "descriptive", "probabilistic", "verified"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number}: record must be an object")
        value["_line"] = line_number
        records.append(value)
    return records


def validate(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for record in records:
        line = record["_line"]
        sample_id = record.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            errors.append(f"line {line}: missing sample_id")
        elif sample_id in seen:
            errors.append(f"line {line}: duplicate sample_id {sample_id}")
        else:
            seen.add(sample_id)

        for field in ("trace_id", "text", "known_conditions", "labels", "provenance_level", "permitted_claim"):
            if field not in record:
                errors.append(f"line {line}: missing {field}")

        conditions = record.get("known_conditions")
        if not isinstance(conditions, dict):
            errors.append(f"line {line}: known_conditions must be an object")
        else:
            missing = REQUIRED_CONDITIONS - set(conditions)
            if missing:
                errors.append(f"line {line}: missing known conditions: {sorted(missing)}")

        labels = record.get("labels")
        if not isinstance(labels, list) or not labels or not all(isinstance(x, str) and x for x in labels):
            errors.append(f"line {line}: labels must be a non-empty string array")

        if record.get("permitted_claim") not in ALLOWED_CLAIMS:
            errors.append(f"line {line}: unsupported permitted_claim")

        # Fail closed: verified attribution requires verified provenance and a known model family.
        if record.get("permitted_claim") == "verified":
            model = (conditions or {}).get("model_family")
            if record.get("provenance_level") != "verified_generation_receipt" or model in {None, "unknown", "none_asserted"}:
                errors.append(f"line {line}: verified claim lacks verified generation provenance")
    return errors


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts: Counter[str] = Counter()
    platforms: Counter[str] = Counter()
    claims: Counter[str] = Counter()
    known_models = 0
    for record in records:
        label_counts.update(record["labels"])
        platforms.update([record["known_conditions"]["platform"]])
        claims.update([record["permitted_claim"]])
        if record["known_conditions"]["model_family"] not in {"unknown", "none_asserted"}:
            known_models += 1
    return {
        "record_count": len(records),
        "unique_label_count": len(label_counts),
        "label_counts": dict(sorted(label_counts.items())),
        "platform_counts": dict(sorted(platforms.items())),
        "permitted_claim_counts": dict(sorted(claims.items())),
        "records_with_known_model_family": known_models,
        "model_classification_ready": known_models >= 2,
        "admissibility_note": "Style features are retained as data; model identity is not inferred without provenance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        records = load_jsonl(args.corpus)
        errors = validate(records)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL {args.corpus}: {exc}")
        return 1

    if errors:
        print(f"FAIL {args.corpus}")
        for error in errors:
            print(f"  - {error}")
        return 1

    report = summarize(records)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
