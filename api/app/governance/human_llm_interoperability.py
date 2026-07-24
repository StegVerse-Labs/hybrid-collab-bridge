"""Governed Human–LLM pair assessment runtime and API.

The pair and its trace are evaluated as one interoperability unit. Admission is
fail-closed for critical structural failures and for missing demonstrated
comprehension on high-consequence claims.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/interoperability", tags=["human-llm-interoperability"])

ADMIN_TOKEN = ""
CGE_PATH = Path("./cge_light")
SESSIONS_ROOT = Path(os.getenv("HCB_SESSIONS_ROOT", "sessions"))

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


class AssessmentSubmission(BaseModel):
    session_path: str
    assessment: dict[str, Any]
    reviewer_action: str | None = None
    reviewer_entity_id: str | None = None


class AssessmentResult(BaseModel):
    assessment_id: str
    trace_id: str
    outcome: str
    admission_decision: str
    publication_allowed: bool
    errors: list[str] = Field(default_factory=list)
    receipt: dict[str, Any]
    session_artifact: str


def configure(admin_token: str, cge_path: Path, sessions_root: Path | None = None) -> None:
    global ADMIN_TOKEN, CGE_PATH, SESSIONS_ROOT
    ADMIN_TOKEN = admin_token
    CGE_PATH = Path(cge_path)
    if sessions_root is not None:
        SESSIONS_ROOT = Path(sessions_root)


def _auth(token: str | None) -> None:
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _recommended_outcome(record: dict[str, Any]) -> str:
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


def validate_assessment(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"assessment_id", "trace_id", "timestamp", "tests", "review", "overall_outcome", "error_attribution"}
    missing = sorted(required - record.keys())
    if missing:
        return [f"missing required fields: {', '.join(missing)}"]
    tests = record.get("tests")
    if not isinstance(tests, dict):
        return ["tests must be an object"]
    if set(tests) != REQUIRED_TESTS:
        missing_tests = sorted(REQUIRED_TESTS - set(tests))
        extra_tests = sorted(set(tests) - REQUIRED_TESTS)
        if missing_tests:
            errors.append(f"missing tests: {', '.join(missing_tests)}")
        if extra_tests:
            errors.append(f"unknown tests: {', '.join(extra_tests)}")
    for name, result in tests.items():
        if not isinstance(result, dict):
            errors.append(f"{name}: result must be an object")
            continue
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
    if record.get("overall_outcome") not in VALID_OUTCOMES:
        errors.append("invalid overall_outcome")
    attrs = record.get("error_attribution")
    if not isinstance(attrs, list):
        errors.append("error_attribution must be an array")
    else:
        invalid = sorted(set(attrs) - VALID_ATTRIBUTIONS)
        if invalid:
            errors.append(f"invalid error attribution: {', '.join(invalid)}")
    if not errors:
        expected = _recommended_outcome(record)
        if record["overall_outcome"] != expected:
            errors.append(f"overall_outcome must be {expected}, got {record['overall_outcome']}")
    return errors


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


def _append_receipt(payload: dict[str, Any], decision: str) -> dict[str, Any]:
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
    receipt_dir = CGE_PATH / "meta" / "receipts"
    chain_path = CGE_PATH / "meta" / "receipt_chains.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    chain_path.parent.mkdir(parents=True, exist_ok=True)

    previous_hash = "GENESIS"
    previous_receipt_id = None
    if ledger_path.exists():
        lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            previous = json.loads(lines[-1])
            previous_hash = previous.get("entry_hash", "GENESIS")
            previous_receipt_id = previous.get("receipt_id")

    receipt_id = f"hllm-{uuid4().hex}"
    ledger_entry_id = f"entry-{uuid4().hex}"
    timestamp = datetime.now(timezone.utc).isoformat()
    entry_material = {
        "ledger_entry_id": ledger_entry_id,
        "receipt_id": receipt_id,
        "timestamp": timestamp,
        "mutation_class": "human_llm_pair_assessment",
        "decision": decision,
        "previous_hash": previous_hash,
        "payload": payload,
    }
    entry_hash = hashlib.sha256(_canonical(entry_material)).hexdigest()
    entry = {**entry_material, "entry_hash": entry_hash, "verified": True}
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")

    receipt = {
        "receipt_id": receipt_id,
        "ledger_entry_id": ledger_entry_id,
        "entry_hash": entry_hash,
        "previous_hash": previous_hash,
        "decision": decision,
        "verified": True,
        "timestamp": timestamp,
        "payload_hash": hashlib.sha256(_canonical(payload)).hexdigest(),
    }
    (receipt_dir / "latest_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    with chain_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "chain_id": payload["trace_id"],
            "receipt_id": receipt_id,
            "previous_receipt_id": previous_receipt_id,
            "entry_hash": entry_hash,
            "previous_hash": previous_hash,
        }, sort_keys=True) + "\n")
    return receipt


@router.post("/assessments", response_model=AssessmentResult)
async def submit_assessment(body: AssessmentSubmission, x_admin_token: str | None = Header(default=None)):
    _auth(x_admin_token)
    session_dir = _resolve_session(body.session_path)
    assessment = json.loads(json.dumps(body.assessment))
    errors = validate_assessment(assessment)
    outcome = assessment.get("overall_outcome", "INDETERMINATE") if not errors else "INDETERMINATE"
    admission_decision = "allow" if not errors and outcome == "PASS" else "defer" if not errors and outcome == "PARTIAL" else "deny"
    publication_allowed = admission_decision == "allow"
    payload = {
        "type": "human_llm_pair_assessment",
        "assessment_id": assessment.get("assessment_id", "missing"),
        "trace_id": assessment.get("trace_id", "missing"),
        "session_path": str(session_dir),
        "outcome": outcome,
        "admission_decision": admission_decision,
        "publication_allowed": publication_allowed,
        "validation_errors": errors,
        "reviewer_action": body.reviewer_action,
        "reviewer_entity_id": body.reviewer_entity_id,
        "assessment_hash": hashlib.sha256(_canonical(assessment)).hexdigest(),
    }
    receipt = _append_receipt(payload, admission_decision)
    artifact = {
        "assessment": assessment,
        "admission": {
            "decision": admission_decision,
            "publication_allowed": publication_allowed,
            "errors": errors,
        },
        "receipt": receipt,
    }
    artifact_path = session_dir / "04_human_llm_pair_assessment.json"
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return AssessmentResult(
        assessment_id=payload["assessment_id"],
        trace_id=payload["trace_id"],
        outcome=outcome,
        admission_decision=admission_decision,
        publication_allowed=publication_allowed,
        errors=errors,
        receipt=receipt,
        session_artifact=str(artifact_path),
    )


@router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str, session_path: str, x_admin_token: str | None = Header(default=None)):
    _auth(x_admin_token)
    session_dir = _resolve_session(session_path)
    artifact_path = session_dir / "04_human_llm_pair_assessment.json"
    if not artifact_path.exists():
        raise HTTPException(404, "Assessment not found")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    if artifact.get("assessment", {}).get("assessment_id") != assessment_id:
        raise HTTPException(404, "Assessment not found")
    return artifact
