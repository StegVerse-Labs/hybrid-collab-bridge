#!/usr/bin/env python3
"""Validate HIL independent-response packets fail-closed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: pip install jsonschema") from exc


UNVALIDATED_INTAKE_STATUS = (
    "recorded_as_repository_evidence_not_yet_validated_or_accepted_for_publication"
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read valid JSON from {path}: {exc}") from exc


def semantic_errors(packet: dict[str, Any]) -> list[str]:
    """Enforce authority rules that cannot be expressed safely by shape alone."""
    errors: list[str] = []
    submission = packet.get("submission_record", {})

    if submission.get("publication_authority") is not False:
        errors.append(
            "submission_record/publication_authority: independent repository evidence "
            "cannot self-grant publication authority"
        )

    if submission.get("master_record_appended") is not False:
        errors.append(
            "submission_record/master_record_appended: append authority requires a "
            "separate verified Master Record receipt"
        )

    if submission.get("intake_status") != UNVALIDATED_INTAKE_STATUS:
        errors.append(
            "submission_record/intake_status: v1 repository intake must remain explicitly "
            "unvalidated and unaccepted until a separate admission transition occurs"
        )

    if packet.get("self_participation", {}).get("narrow_structural_participation") is not True:
        errors.append(
            "self_participation/narrow_structural_participation: the packet must state its "
            "own narrow structural participation"
        )

    return errors


def validate_packet(packet_path: Path, schema_path: Path) -> list[str]:
    packet = load_json(packet_path)
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(packet), key=lambda item: list(item.path))
    rendered = [
        f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
        for error in errors
    ]
    if not errors and isinstance(packet, dict):
        rendered.extend(semantic_errors(packet))
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/hil_independent_response.schema.json"),
    )
    args = parser.parse_args()

    try:
        errors = validate_packet(args.packet, args.schema)
    except ValueError as exc:
        print(f"DENY: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("DENY: independent response packet failed validation", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"PASS: {args.packet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
