#!/usr/bin/env python3
"""Validate governed style experiment intake packets before execution or publication."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/style_experiment_intake.schema.json"


def validate(packet: dict[str, Any], schema: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema
        jsonschema.validate(packet, schema)
    except ImportError:
        return ["jsonschema dependency missing"]
    except jsonschema.ValidationError as exc:
        return [f"schema: {exc.message}"]

    models = packet["participants"]["model_systems"]
    declared_families = {model["model_family"] for model in models}
    if len(declared_families) < 2:
        errors.append("at least two distinct model families are required")

    sample_ids = [sample["sample_id"] for sample in packet["samples"]]
    duplicates = sorted(sample_id for sample_id, count in Counter(sample_ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate sample_id values: {', '.join(duplicates)}")

    counts: Counter[tuple[str, str]] = Counter()
    for sample in packet["samples"]:
        family = sample["model_family"]
        if family not in declared_families:
            errors.append(f"sample {sample['sample_id']} references undeclared model family {family}")
        counts[(family, sample["phase"])] += 1
        for field in ("text_path", "receipt_path"):
            candidate = (root / sample[field]).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                errors.append(f"sample {sample['sample_id']} {field} escapes packet root")
                continue
            if not candidate.is_file():
                errors.append(f"sample {sample['sample_id']} missing {field}: {sample[field]}")

    for family in sorted(declared_families):
        if counts[(family, "baseline")] < 1:
            errors.append(f"model family {family} requires at least one baseline sample")
        if counts[(family, "followup")] < 1:
            errors.append(f"model family {family} requires at least one followup sample")

    public = packet["publication_posture"] == "public"
    if public and any(sample.get("human_revision_applied") and sample["phase"] == "baseline" for sample in packet["samples"]):
        errors.append("public baseline samples cannot be marked human_revision_applied")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_style_experiment_intake.py PACKET.json", file=sys.stderr)
        return 2
    packet_path = Path(argv[1])
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        if not isinstance(packet, dict):
            raise ValueError("packet must be a JSON object")
        errors = validate(packet, schema, packet_path.parent)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print(f"FAIL {packet_path}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS {packet_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
