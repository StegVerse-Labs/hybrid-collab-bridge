"""Schema validation and authenticated evidence persistence for Human–LLM assessments."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .receipt_signing import ReceiptSigner, verification_metadata

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


def _receipt_hash_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    excluded = {
        "receipt_hash",
        "signer_id",
        "key_ref",
        "signature_algorithm",
        "signature",
    }
    return {key: value for key, value in receipt.items() if key not in excluded}


def verify_mediated_receipt(receipt: dict[str, Any], signer: ReceiptSigner) -> dict[str, Any]:
    declared_hash = receipt.get("receipt_hash")
    expected_hash = sha256_json(_receipt_hash_payload(receipt))
    signature = verification_metadata(receipt, signer)
    hash_verified = isinstance(declared_hash, str) and declared_hash == expected_hash
    return {
        **signature,
        "hash_verified": hash_verified,
        "verified": bool(signature["verified"] and hash_verified),
        "receipt_hash": declared_hash,
    }


def verify_mediated_chain(
    receipts: list[dict[str, Any]], signer: ReceiptSigner, genesis_hash: str = GENESIS_HASH
) -> dict[str, Any]:
    previous_hash = genesis_hash
    results: list[dict[str, Any]] = []
    for expected_sequence, receipt in enumerate(receipts, start=1):
        result = verify_mediated_receipt(receipt, signer)
        result["sequence_verified"] = receipt.get("sequence") == expected_sequence
        result["previous_hash_verified"] = receipt.get("previous_hash") == previous_hash
        result["participant_id"] = receipt.get("participant_id")
        result["verified"] = bool(
            result["verified"]
            and result["sequence_verified"]
            and result["previous_hash_verified"]
        )
        results.append(result)
        previous_hash = str(receipt.get("receipt_hash", ""))
    return {
        "verified": bool(receipts) and all(result["verified"] for result in results),
        "count": len(receipts),
        "chain_head": previous_hash,
        "genesis_hash": genesis_hash,
        "results": results,
    }


def build_mediated_receipts(
    record: dict[str, Any],
    previous_hash: str = GENESIS_HASH,
    signer: ReceiptSigner | None = None,
) -> tuple[list[dict[str, Any]], str]:
    mediated = record.get("mediated_composition")
    if not isinstance(mediated, dict):
        return [], previous_hash
    local = mediated.get("local_admissibility", [])
    if not all(isinstance(item, dict) for item in local):
        raise ValueError("local_admissibility entries must be objects")
    active_signer = signer or ReceiptSigner.from_environment(required=True)
    assert active_signer is not None

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
        unsigned_receipt = {**payload, "receipt_hash": receipt_hash}
        receipt = {**unsigned_receipt, **active_signer.sign(unsigned_receipt)}
        receipts.append(receipt)
        chain_hash = receipt_hash
    return receipts, chain_hash


def persist_mediated_receipts(
    record: dict[str, Any],
    session_dir: Path,
    signer: ReceiptSigner | None = None,
) -> dict[str, Any] | None:
    active_signer = signer
    if isinstance(record.get("mediated_composition"), dict) and active_signer is None:
        active_signer = ReceiptSigner.from_environment(required=True)
    receipts, chain_head = build_mediated_receipts(record, signer=active_signer)
    if not receipts:
        return None
    assert active_signer is not None
    verification = verify_mediated_chain(receipts, active_signer)
    if not verification["verified"]:
        raise ValueError("generated mediated receipt chain failed signature or continuity verification")

    path = session_dir / "05_mediated_transition_receipts.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for receipt in receipts:
            handle.write(canonical_json(receipt) + "\n")
    verification_path = session_dir / "06_mediated_transition_verification.json"
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    return {
        "path": str(path),
        "verification_path": str(verification_path),
        "count": len(receipts),
        "chain_head": chain_head,
        "assessment_hash": receipts[0]["assessment_hash"],
        "receipt_hashes": [receipt["receipt_hash"] for receipt in receipts],
        "signer_id": active_signer.signer_id,
        "key_ref": active_signer.key_ref,
        "signature_algorithm": active_signer.algorithm,
        "signatures_verified": verification["verified"],
    }
