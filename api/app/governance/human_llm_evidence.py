"""Schema validation and deterministic evidence persistence for Human–LLM assessments."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

GENESIS_HASH = "0" * 64
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "human_llm_pair_assessment.schema.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_schema(record: dict[str, Any], schema_path: Path | None = None) -> list[str]:
    path = schema_path or SCHEMA_PATH
    if not path.exists():
        return [f"assessment schema not found: {path}"]
    schema = json.loads(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.absolute_path))
    rendered: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"schema:{location}: {error.message}")
    return rendered


def build_mediated_receipts(
    record: dict[str, Any], previous_hash: str = GENESIS_HASH
) -> tuple[list[dict[str, Any]], str]:
    mediated = record.get("mediated_composition")
    if not isinstance(mediated, dict):
        return [], previous_hash
    local = mediated.get("local_admissibility", [])
    if not all(isinstance(item, dict) for item in local):
        raise ValueError("local_admissibility entries must be objects")

    receipts: list[dict[str, Any]] = []
    chain_hash = previous_hash
    assessment_hash = sha256_json(record)
    for sequence, decision in enumerate(local, start=1):
        payload = {
            "receipt_type": "mediated_local_admissibility",
            "assessment_id": record.get("assessment_id"),
            "trace_id": record.get("trace_id"),
            "timestamp": record.get("timestamp"),
            "sequence": sequence,
            "participant_id": decision.get("participant_id"),
            "decision": decision.get("decision"),
            "policy_ref": decision.get("policy_ref"),
            "evidence": decision.get("evidence", []),
            "declared_receipt_ref": decision.get("receipt_ref"),
            "claimed_level": mediated.get("claimed_level"),
            "assessment_hash": assessment_hash,
            "previous_hash": chain_hash,
        }
        receipt_hash = sha256_json(payload)
        receipt = {**payload, "receipt_hash": receipt_hash}
        receipts.append(receipt)
        chain_hash = receipt_hash
    return receipts, chain_hash


def persist_mediated_receipts(
    record: dict[str, Any], session_dir: Path
) -> dict[str, Any] | None:
    receipts, chain_head = build_mediated_receipts(record)
    if not receipts:
        return None
    path = session_dir / "05_mediated_transition_receipts.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for receipt in receipts:
            handle.write(canonical_json(receipt) + "\n")
    return {
        "path": str(path),
        "count": len(receipts),
        "chain_head": chain_head,
        "assessment_hash": receipts[0]["assessment_hash"],
        "receipt_hashes": [receipt["receipt_hash"] for receipt in receipts],
    }
