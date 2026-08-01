#!/usr/bin/env python3
"""Dependency-light validator for HIL qualified-recognition receipts.

Validates the canonical receipt shape and the bounded semantic activation gates.
It intentionally does not grant final admissibility, identity, publication, or
execution authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_STATUS = {
    "candidate", "pending_validation", "pending_admission", "admitted", "denied", "superseded"
}
ALLOWED_CONSENT = {
    "unknown", "observation_only", "attribution_allowed", "research_use_allowed",
    "publication_allowed", "withdrawn"
}
ALLOWED_ADMISSION = {"not_requested", "pending", "ALLOW", "DENY", "ERROR"}
STANDING = {
    "observer", "contributor_candidate", "recognized_contributor",
    "continuing_participant", "reviewer_candidate"
}
REQUIRED_TOP = {
    "receipt_id", "trace_id", "capability_id", "status", "contributor", "contribution",
    "qualified_examination", "causal_effect", "attribution", "consent_posture",
    "standing_transition", "scope_boundary", "replay", "admission", "custody"
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def refs(value: Any, *, minimum: int = 1) -> bool:
    return isinstance(value, list) and len(value) >= minimum and all(nonempty(v) for v in value)


def validate(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP - set(receipt))
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(missing)}")
        return errors

    if receipt.get("capability_id") != "HIL-QRL-001":
        errors.append("capability_id must equal HIL-QRL-001")
    if receipt.get("status") not in ALLOWED_STATUS:
        errors.append("invalid status")
    if receipt.get("consent_posture") not in ALLOWED_CONSENT:
        errors.append("invalid consent_posture")

    contributor = receipt.get("contributor")
    if not isinstance(contributor, dict) or not nonempty(contributor.get("participant_ref")):
        errors.append("contributor.participant_ref must be non-empty")

    contribution = receipt.get("contribution")
    if not isinstance(contribution, dict):
        errors.append("contribution must be an object")
    else:
        for key in ("contribution_ref", "description"):
            if not nonempty(contribution.get(key)):
                errors.append(f"contribution.{key} must be non-empty")
        if not refs(contribution.get("evidence_refs")):
            errors.append("contribution.evidence_refs must contain at least one reference")

    examination = receipt.get("qualified_examination")
    if not isinstance(examination, dict):
        errors.append("qualified_examination must be an object")
    else:
        for key in ("reconstruction_statement", "qualification_basis"):
            if not nonempty(examination.get(key)):
                errors.append(f"qualified_examination.{key} must be non-empty")
        if not refs(examination.get("evidence_refs")):
            errors.append("qualified_examination.evidence_refs must contain evidence")

    causal = receipt.get("causal_effect")
    if not isinstance(causal, dict):
        errors.append("causal_effect must be an object")
    else:
        if not nonempty(causal.get("result_ref")):
            errors.append("causal_effect.result_ref must be non-empty")
        if causal.get("material_effect") is not True:
            errors.append("causal_effect.material_effect must be true for recognition candidacy")
        if not nonempty(causal.get("bounded_claim")):
            errors.append("causal_effect.bounded_claim must be non-empty")
        if causal.get("reconstructable") is not True:
            errors.append("causal_effect.reconstructable must be true")
        if not refs(causal.get("evidence_refs")):
            errors.append("causal_effect.evidence_refs must contain evidence")

    attribution = receipt.get("attribution")
    if not isinstance(attribution, dict) or attribution.get("preserved") is not True:
        errors.append("attribution.preserved must be true")
    elif not nonempty(attribution.get("attribution_ref")):
        errors.append("attribution.attribution_ref must be non-empty")

    consent = receipt.get("consent_posture")
    if consent in {"unknown", "withdrawn"}:
        errors.append("consent_posture does not permit recognition processing")

    transition = receipt.get("standing_transition")
    if not isinstance(transition, dict):
        errors.append("standing_transition must be an object")
    else:
        if transition.get("prior") not in STANDING or transition.get("proposed") not in STANDING:
            errors.append("standing_transition prior/proposed value is invalid")
        if not nonempty(transition.get("scope")):
            errors.append("standing_transition.scope must be non-empty")
        if transition.get("prior") == transition.get("proposed"):
            errors.append("standing_transition must represent an actual bounded transition")

    boundary = receipt.get("scope_boundary")
    if not isinstance(boundary, dict):
        errors.append("scope_boundary must be an object")
    else:
        for key in (
            "representative_authority_claimed", "execution_authority_claimed",
            "publication_authority_claimed", "final_admissibility_claimed"
        ):
            if boundary.get(key) is not False:
                errors.append(f"scope_boundary.{key} must be false")

    replay = receipt.get("replay")
    if not isinstance(replay, dict) or not refs(replay.get("input_refs")):
        errors.append("replay.input_refs must contain at least one reference")
    elif not nonempty(replay.get("deterministic_profile")):
        errors.append("replay.deterministic_profile must be non-empty")

    admission = receipt.get("admission")
    if not isinstance(admission, dict) or admission.get("state") not in ALLOWED_ADMISSION:
        errors.append("admission.state is invalid")
    elif admission.get("state") in {"ALLOW", "DENY", "ERROR"} and not nonempty(admission.get("decision_ref")):
        errors.append("terminal admission state requires admission.decision_ref")

    custody = receipt.get("custody")
    if not isinstance(custody, dict) or "destination" not in custody or "receipt_ref" not in custody:
        errors.append("custody must contain destination and receipt_ref")

    return errors


def canonical_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipts", nargs="+", type=Path)
    parser.add_argument("--expect-invalid", action="store_true")
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args()

    results = []
    overall = True
    for path in args.receipts:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("top-level JSON must be an object")
            errors = validate(data)
            valid = not errors
            expectation_met = (not valid) if args.expect_invalid else valid
            overall = overall and expectation_met
            results.append({
                "path": path.as_posix(),
                "valid": valid,
                "expectation": "invalid" if args.expect_invalid else "valid",
                "expectation_met": expectation_met,
                "canonical_sha256": canonical_digest(data),
                "errors": errors,
            })
        except Exception as exc:  # deterministic failure record
            expectation_met = args.expect_invalid
            overall = overall and expectation_met
            results.append({
                "path": path.as_posix(), "valid": False,
                "expectation": "invalid" if args.expect_invalid else "valid",
                "expectation_met": expectation_met, "canonical_sha256": None,
                "errors": [f"parse_error: {exc}"],
            })

    report = {
        "validator": "HIL-QRL-001-validator-v1",
        "deterministic": True,
        "overall_expectation_met": overall,
        "results": results,
        "authority_boundary": {
            "grants_final_admissibility": False,
            "grants_identity": False,
            "grants_execution_authority": False,
            "grants_publication_authority": False,
        },
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.receipt_out:
        args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_out.write_text(text, encoding="utf-8")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
