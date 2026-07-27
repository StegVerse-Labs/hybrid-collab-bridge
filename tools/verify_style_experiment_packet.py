#!/usr/bin/env python3
"""Verify a complete HIL style-experiment packet before execution.

This command composes intake validation with cryptographic receipt verification and
sample-to-receipt binding. It emits a machine-readable readiness report and fails
closed when any artifact, provenance claim, phase, or model binding is inconsistent.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from validate_style_experiment_intake import validate as validate_intake

ROOT = Path(__file__).resolve().parents[1]
INTAKE_SCHEMA = ROOT / "schemas/style_experiment_intake.schema.json"
RECEIPT_SCHEMA = ROOT / "schemas/style_generation_receipt.schema.json"


def canonical_payload(record: dict[str, Any]) -> bytes:
    return json.dumps(
        {key: value for key, value in record.items() if key != "signature"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_receipt(
    receipt: dict[str, Any],
    receipt_schema: dict[str, Any],
    text: str,
    sample: dict[str, Any],
    key: str,
) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema
        jsonschema.validate(receipt, receipt_schema, format_checker=jsonschema.FormatChecker())
    except ImportError:
        return ["jsonschema dependency missing"]
    except jsonschema.ValidationError as exc:
        return [f"receipt schema: {exc.message}"]

    sample_id = sample["sample_id"]
    if receipt.get("sample_id") != sample_id:
        errors.append("receipt sample_id does not match packet sample_id")
    if receipt.get("model_family") != sample["model_family"]:
        errors.append("receipt model_family does not match packet model_family")
    if receipt.get("output_hash") != sha256_text(text):
        errors.append("receipt output_hash does not match sample text")

    expected_revision = bool(sample.get("human_revision_applied", False))
    receipt_revision = bool((receipt.get("human_revision") or {}).get("applied", False))
    if receipt_revision != expected_revision:
        errors.append("receipt human_revision state does not match packet sample")

    if receipt.get("provenance_level") != "cryptographically_bound":
        errors.append("receipt provenance_level must be cryptographically_bound")
    signature = receipt.get("signature") or {}
    if signature.get("algorithm") != "hmac-sha256":
        errors.append("receipt signature algorithm must be hmac-sha256")
    else:
        expected = hmac.new(key.encode("utf-8"), canonical_payload(receipt), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, str(signature.get("value", ""))):
            errors.append("receipt signature verification failed")
    return [f"{sample_id}: {error}" for error in errors]


def verify(packet_path: Path, key: str) -> dict[str, Any]:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    intake_schema = json.loads(INTAKE_SCHEMA.read_text(encoding="utf-8"))
    receipt_schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    root = packet_path.parent

    errors = validate_intake(packet, intake_schema, root)
    verified_samples: list[dict[str, Any]] = []
    if not errors:
        for sample in packet["samples"]:
            text_path = root / sample["text_path"]
            receipt_path = root / sample["receipt_path"]
            try:
                text = text_path.read_text(encoding="utf-8")
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{sample['sample_id']}: artifact load failed: {exc}")
                continue
            sample_errors = verify_receipt(receipt, receipt_schema, text, sample, key)
            errors.extend(sample_errors)
            verified_samples.append({
                "sample_id": sample["sample_id"],
                "phase": sample["phase"],
                "model_family": sample["model_family"],
                "text_sha256": sha256_text(text),
                "receipt_id": receipt.get("receipt_id"),
                "verified": not sample_errors,
            })

    ready = not errors and len(verified_samples) == len(packet.get("samples", []))
    return {
        "experiment_id": packet.get("experiment_id"),
        "protocol_version": packet.get("protocol_version"),
        "status": "READY" if ready else "BLOCKED",
        "execution_admissible": ready,
        "publication_admissible": ready and packet.get("publication_posture") == "public",
        "publication_posture": packet.get("publication_posture"),
        "verified_samples": verified_samples,
        "claim_boundary": packet.get("claim_boundary"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet")
    parser.add_argument("--output")
    args = parser.parse_args()
    key = os.getenv("HCB_STYLE_RECEIPT_KEY")
    if not key:
        raise SystemExit("HCB_STYLE_RECEIPT_KEY is required")
    try:
        report = verify(Path(args.packet), key)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report = {
            "experiment_id": None,
            "status": "BLOCKED",
            "execution_admissible": False,
            "publication_admissible": False,
            "errors": [str(exc)],
        }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
