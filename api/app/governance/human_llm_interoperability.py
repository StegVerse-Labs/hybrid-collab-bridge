"""Governed Human–LLM pair assessment runtime and API.

The human/model pair and its trace are evaluated as one interoperability unit.
Structural admission is fail-closed, schema-enforced, and then passed through
the bridge's canonical BCAT/GCAT AdmissionGate and CGELightClient receipt path.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .admission import AdmissionGate
from .cge_client import CGELightClient
from .entity import EntityIdentity
from .human_llm_evidence import persist_mediated_receipts, validate_schema

router = APIRouter(prefix="/v1/interoperability", tags=["human-llm-interoperability"])

ADMIN_TOKEN = ""
CGE_PATH = Path("./cge_light")
SESSIONS_ROOT = Path(os.getenv("HCB_SESSIONS_ROOT", "sessions"))
CGE_CLIENT: CGELightClient | None = None
ADMISSION_GATE: AdmissionGate | None = None
ASSESSOR_ENTITY: EntityIdentity | None = None

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
    "continuity_originated",
    "mediation_originated",
    "provenance_originated",
    "agency_inflation",
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
    bcat: dict[str, Any] = Field(default_factory=dict)
    gcat: dict[str, Any] = Field(default_factory=dict)
    receipt: dict[str, Any]
    session_artifact: str
    mediated_receipts: dict[str, Any] | None = None


def configure(
    admin_token: str,
    cge_path: Path,
    sessions_root: Path | None = None,
    cge_client: CGELightClient | None = None,
    admission_gate: AdmissionGate | None = None,
    assessor_entity: EntityIdentity | None = None,
) -> None:
    global ADMIN_TOKEN, CGE_PATH, SESSIONS_ROOT, CGE_CLIENT, ADMISSION_GATE, ASSESSOR_ENTITY
    ADMIN_TOKEN = admin_token
    CGE_PATH = Path(cge_path)
    if sessions_root is not None:
        SESSIONS_ROOT = Path(sessions_root)
    CGE_CLIENT = cge_client or CGELightClient(
        org_id=os.getenv("HCB_ORG_ID", "StegVerse-Labs"),
        mode=os.getenv("HCB_CGE_MODE", "embedded"),
        endpoint=os.getenv("HCB_CGE_ENDPOINT") or None,
        cge_path=str(CGE_PATH),
    )
    if admission_gate is not None:
        ADMISSION_GATE = admission_gate
    else:
        constitution_path = CGE_PATH / "repo_constitution.txt"
        constitution: dict[str, Any] = {}
        if constitution_path.exists():
            import yaml
            constitution = yaml.safe_load(constitution_path.read_text(encoding="utf-8")) or {}
        ADMISSION_GATE = AdmissionGate(CGE_CLIENT, constitution)
    ASSESSOR_ENTITY = assessor_entity or EntityIdentity(
        entity_id="human-llm-pair-assessor",
        entity_type="automated_process",
        org_id=os.getenv("HCB_ORG_ID", "StegVerse-Labs"),
        owner_human=os.getenv("HCB_OWNER_HUMAN", "owner"),
        owner_ai=os.getenv("HCB_OWNER_AI", "Beta_Orionis"),
        capability_set=["human-llm-assessment", "admission", "receipt"],
        governance_scope="internal",
    )


def _auth(token: str | None) -> None:
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


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


def validate_assessment(record: dict[str, Any]) -> list[str]:
    errors = validate_schema(record)
    required = {"assessment_id", "trace_id", "timestamp", "tests", "review", "overall_outcome", "error_attribution"}
    missing = sorted(required - record.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors
    tests = record.get("tests")
    if not isinstance(tests, dict):
        errors.append("tests must be an object")
        return errors
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
        expected = recommended_outcome(record)
        if record["overall_outcome"] != expected:
            errors.append(f"overall_outcome must be {expected}, got {record['overall_outcome']}")
    return list(dict.fromkeys(errors))


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


def _structural_decision(errors: list[str], outcome: str) -> str:
    if errors or outcome in {"FAIL", "INDETERMINATE"}:
        return "deny"
    if outcome == "PARTIAL":
        return "defer"
    return "allow"


async def govern_assessment(
    assessment: dict[str, Any],
    session_dir: Path,
    reviewer_action: str | None = None,
    reviewer_entity_id: str | None = None,
) -> AssessmentResult:
    if ADMISSION_GATE is None or ASSESSOR_ENTITY is None:
        configure(ADMIN_TOKEN, CGE_PATH)
    errors = validate_assessment(assessment)
    outcome = assessment.get("overall_outcome", "INDETERMINATE") if not errors else "INDETERMINATE"
    structural_decision = _structural_decision(errors, outcome)
    mediated_receipts = None
    if not errors:
        try:
            mediated_receipts = persist_mediated_receipts(assessment, session_dir)
        except (OSError, ValueError) as exc:
            errors.append(f"mediated receipt persistence failed: {exc}")
            outcome = "INDETERMINATE"
            structural_decision = "deny"

    payload = {
        "type": "human_llm_pair_assessment",
        "assessment_id": assessment.get("assessment_id", "missing"),
        "trace_id": assessment.get("trace_id", "missing"),
        "session_path": str(session_dir),
        "outcome": outcome,
        "structural_decision": structural_decision,
        "validation_errors": errors,
        "reviewer_action": reviewer_action,
        "reviewer_entity_id": reviewer_entity_id,
        "assessment_hash": hashlib.sha256(_canonical(assessment)).hexdigest(),
        "mediated_receipts": mediated_receipts,
        "assessment": assessment,
    }
    canonical = await ADMISSION_GATE.admit_proposal(
        proposal=payload,
        actor=ASSESSOR_ENTITY,
        source="hybrid-collab-bridge/human-llm-interoperability",
    )
    decision = structural_decision
    if structural_decision == "allow" and canonical.decision != "allow":
        decision = canonical.decision
    elif structural_decision == "defer" and canonical.decision == "deny":
        decision = "deny"
    publication_allowed = decision == "allow"
    artifact = {
        "assessment": assessment,
        "admission": {
            "decision": decision,
            "structural_decision": structural_decision,
            "canonical_decision": canonical.decision,
            "publication_allowed": publication_allowed,
            "errors": errors,
            "reasoning": canonical.reasoning,
            "bcat": canonical.bcat,
            "gcat": canonical.gcat,
        },
        "mediated_receipts": mediated_receipts,
        "receipt": canonical.receipt,
    }
    artifact_path = session_dir / "04_human_llm_pair_assessment.json"
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return AssessmentResult(
        assessment_id=payload["assessment_id"],
        trace_id=payload["trace_id"],
        outcome=outcome,
        admission_decision=decision,
        publication_allowed=publication_allowed,
        errors=errors,
        bcat=canonical.bcat,
        gcat=canonical.gcat,
        receipt=canonical.receipt,
        session_artifact=str(artifact_path),
        mediated_receipts=mediated_receipts,
    )


@router.post("/assessments", response_model=AssessmentResult)
async def submit_assessment(body: AssessmentSubmission, x_admin_token: str | None = Header(default=None)):
    _auth(x_admin_token)
    session_dir = _resolve_session(body.session_path)
    assessment = json.loads(json.dumps(body.assessment))
    return await govern_assessment(
        assessment,
        session_dir,
        reviewer_action=body.reviewer_action,
        reviewer_entity_id=body.reviewer_entity_id,
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
