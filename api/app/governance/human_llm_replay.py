"""Deterministic replay and independent verification for Human–LLM assessments.

Replay reads only persisted session artifacts and configured verification material. It
never reuses an in-memory admission result and therefore provides a bounded test of
whether the governed record can be reconstructed independently.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from .human_llm_evidence import sha256_json, validate_schema, verify_mediated_chain
from .receipt_signing import ReceiptSigner

router = APIRouter(prefix="/v1/interoperability", tags=["human-llm-interoperability-replay"])

ADMIN_TOKEN = ""
SESSIONS_ROOT = Path("sessions")
HIGH_CONSEQUENCE = {"high", "critical"}


def configure_replay(admin_token: str, sessions_root: Path | None = None) -> None:
    global ADMIN_TOKEN, SESSIONS_ROOT
    ADMIN_TOKEN = admin_token
    if sessions_root is not None:
        SESSIONS_ROOT = Path(sessions_root)


def _auth(token: str | None) -> None:
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _resolve_session(session_path: str) -> Path:
    candidate = Path(session_path).expanduser().resolve()
    root = SESSIONS_ROOT.expanduser().resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(400, "session_path must be inside configured sessions root") from exc
    if not candidate.exists() or not candidate.is_dir():
        raise HTTPException(404, "Session path not found")
    return candidate


def _recommended_outcome(record: dict[str, Any]) -> str:
    tests = record.get("tests", {})
    statuses = [test.get("status") for test in tests.values() if isinstance(test, dict)]
    if any(test.get("critical") and test.get("status") == "FAIL" for test in tests.values() if isinstance(test, dict)):
        return "FAIL"
    if any(
        test.get("critical") and test.get("status") == "INDETERMINATE"
        for test in tests.values()
        if isinstance(test, dict)
    ):
        return "INDETERMINATE"
    review = record.get("review", {})
    if record.get("claim_consequence") in HIGH_CONSEQUENCE and not review.get("comprehension_demonstrated"):
        return "FAIL"
    if "INDETERMINATE" in statuses:
        return "INDETERMINATE"
    if "FAIL" in statuses or "PARTIAL" in statuses:
        return "PARTIAL"
    return "PASS"


def _structural_decision(schema_errors: list[str], outcome: str) -> str:
    if schema_errors or outcome in {"FAIL", "INDETERMINATE"}:
        return "deny"
    if outcome == "PARTIAL":
        return "defer"
    return "allow"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _read_receipts(path: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read {path.name}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(receipt, dict):
            raise ValueError(f"{path.name}:{line_number}: receipt must be an object")
        receipts.append(receipt)
    return receipts


def replay_assessment(session_dir: Path, assessment_id: str) -> dict[str, Any]:
    artifact_path = session_dir / "04_human_llm_pair_assessment.json"
    if not artifact_path.exists():
        raise ValueError("assessment artifact not found")
    artifact = _read_json(artifact_path)
    assessment = artifact.get("assessment")
    admission = artifact.get("admission")
    if not isinstance(assessment, dict) or not isinstance(admission, dict):
        raise ValueError("assessment artifact is missing assessment or admission object")
    if assessment.get("assessment_id") != assessment_id:
        raise ValueError("assessment_id does not match persisted artifact")

    schema_errors = validate_schema(assessment)
    assessment_hash = sha256_json(assessment)
    declared_reference = artifact.get("mediated_receipts")
    declared_assessment_hash = (
        declared_reference.get("assessment_hash") if isinstance(declared_reference, dict) else None
    )
    assessment_hash_verified = declared_assessment_hash in {None, assessment_hash}

    expected_outcome = _recommended_outcome(assessment) if not schema_errors else "INDETERMINATE"
    outcome_verified = assessment.get("overall_outcome") == expected_outcome
    expected_structural = _structural_decision(schema_errors, expected_outcome)
    structural_verified = admission.get("structural_decision") == expected_structural

    mediated_present = isinstance(assessment.get("mediated_composition"), dict)
    receipt_verification: dict[str, Any] | None = None
    receipt_errors: list[str] = []
    if mediated_present:
        receipts_path = session_dir / "05_mediated_transition_receipts.jsonl"
        if not receipts_path.exists():
            receipt_errors.append("mediated receipt chain not found")
        else:
            signer = ReceiptSigner.from_environment(required=True)
            assert signer is not None
            receipts = _read_receipts(receipts_path)
            receipt_verification = verify_mediated_chain(receipts, signer)
            if not receipt_verification.get("verified"):
                receipt_errors.append("mediated receipt chain verification failed")
            receipt_assessment_hashes = {receipt.get("assessment_hash") for receipt in receipts}
            if receipt_assessment_hashes != {assessment_hash}:
                receipt_errors.append("receipt assessment hash does not match replayed assessment")
            if isinstance(declared_reference, dict):
                if declared_reference.get("chain_head") != receipt_verification.get("chain_head"):
                    receipt_errors.append("persisted chain head does not match reconstructed chain head")
                if declared_reference.get("count") != receipt_verification.get("count"):
                    receipt_errors.append("persisted receipt count does not match reconstructed count")

    canonical_decision = admission.get("canonical_decision")
    stored_decision = admission.get("decision")
    if expected_structural == "allow":
        expected_final = canonical_decision
    elif expected_structural == "defer" and canonical_decision == "deny":
        expected_final = "deny"
    else:
        expected_final = expected_structural
    decision_verified = stored_decision == expected_final
    publication_verified = admission.get("publication_allowed") == (stored_decision == "allow")

    checks = {
        "schema_verified": not schema_errors,
        "assessment_hash_verified": assessment_hash_verified,
        "outcome_verified": outcome_verified,
        "structural_decision_verified": structural_verified,
        "canonical_decision_reconciled": decision_verified,
        "publication_status_verified": publication_verified,
        "receipt_chain_verified": (
            not mediated_present
            or bool(receipt_verification and receipt_verification.get("verified") and not receipt_errors)
        ),
    }
    errors = [*schema_errors, *receipt_errors]
    for name, passed in checks.items():
        if not passed:
            errors.append(f"replay check failed: {name}")

    result = {
        "assessment_id": assessment_id,
        "trace_id": assessment.get("trace_id"),
        "replay_status": "IDENTICAL" if all(checks.values()) else "MISMATCH",
        "reconstructable": all(checks.values()),
        "checks": checks,
        "errors": list(dict.fromkeys(errors)),
        "assessment_hash": assessment_hash,
        "stored": {
            "outcome": assessment.get("overall_outcome"),
            "structural_decision": admission.get("structural_decision"),
            "canonical_decision": canonical_decision,
            "decision": stored_decision,
            "publication_allowed": admission.get("publication_allowed"),
        },
        "reconstructed": {
            "outcome": expected_outcome,
            "structural_decision": expected_structural,
            "decision": expected_final,
            "publication_allowed": stored_decision == "allow",
        },
        "receipt_verification": receipt_verification,
        "source_artifact": str(artifact_path),
    }
    replay_path = session_dir / "07_human_llm_replay_verification.json"
    replay_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["replay_artifact"] = str(replay_path)
    return result


@router.post("/replay/{assessment_id}")
async def replay_endpoint(
    assessment_id: str,
    session_path: str,
    x_admin_token: str | None = Header(default=None),
):
    _auth(x_admin_token)
    session_dir = _resolve_session(session_path)
    try:
        return replay_assessment(session_dir, assessment_id)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/replay/{assessment_id}")
async def get_replay_endpoint(
    assessment_id: str,
    session_path: str,
    x_admin_token: str | None = Header(default=None),
):
    _auth(x_admin_token)
    session_dir = _resolve_session(session_path)
    replay_path = session_dir / "07_human_llm_replay_verification.json"
    if not replay_path.exists():
        raise HTTPException(404, "Replay artifact not found")
    replay = _read_json(replay_path)
    if replay.get("assessment_id") != assessment_id:
        raise HTTPException(404, "Replay artifact not found")
    return replay
