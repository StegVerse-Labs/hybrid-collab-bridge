#!/usr/bin/env python3
"""Validate Human–LLM pair and mediated-composition assessment records.

Critical failures, missing comprehension, incomplete traces, unsupported level
escalation, broken continuity, and inadmissible local transitions take
precedence over numeric averages.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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
LEVELS = [
    "influence",
    "relay",
    "semantic_mediation",
    "adaptive_interoperability",
    "governed_composition",
    "collective_agency",
]
LEVEL_RANK = {name: index for index, name in enumerate(LEVELS)}
REQUIRED_CONTROLS = {
    "paraphrase",
    "intermediary_substitution",
    "relay_delay",
    "hidden_provenance",
    "adversarial_relay",
    "independent_convergence",
}
JOINT_AGENCY_FIELDS = {
    "persistent_joint_state",
    "integrated_objective_selection",
    "shared_memory_or_continuity",
    "joint_decision_boundary",
    "joint_error_correction",
    "accountable_joint_action",
}


def supported_mediated_level(mediated: dict[str, Any]) -> str:
    """Return the highest evidenced level without trusting claimed_level."""
    participants = mediated.get("participants", [])
    channel = mediated.get("channel", {})
    if len(participants) < 3 or not channel.get("observations"):
        return "influence"

    level = "relay"
    fidelity = mediated.get("fidelity", {})
    semantic_dimensions = ("semantic", "pragmatic", "causal")
    if all(isinstance(fidelity.get(key), (int, float)) and fidelity[key] >= 0.7 for key in semantic_dimensions) and fidelity.get("evidence"):
        level = "semantic_mediation"
    else:
        return level

    controls = mediated.get("controls", {})
    adaptation = mediated.get("adaptation_evidence", [])
    null_models = mediated.get("null_models", [])
    null_control_present = any(
        item.get("tested") is True and item.get("result") in {"rejected", "not_rejected", "inconclusive"}
        for item in null_models
        if isinstance(item, dict)
    )
    if adaptation and controls.get("paraphrase") and controls.get("intermediary_substitution") and null_control_present:
        level = "adaptive_interoperability"
    else:
        return level

    continuity = mediated.get("continuity", [])
    local = mediated.get("local_admissibility", [])
    continuity_verified = continuity and all(item.get("status") == "verified" and item.get("evidence") for item in continuity)
    local_allowed = local and all(
        item.get("decision") == "allow" and item.get("policy_ref") and item.get("receipt_ref") and item.get("evidence")
        for item in local
    )
    governance_fidelity = fidelity.get("governance")
    if continuity_verified and local_allowed and isinstance(governance_fidelity, (int, float)) and governance_fidelity >= 0.7:
        level = "governed_composition"
    else:
        return level

    agency = mediated.get("joint_agency_evidence", {})
    if mediated.get("collective_agency_claim") and all(agency.get(field) is True for field in JOINT_AGENCY_FIELDS):
        level = "collective_agency"
    return level


def validate_mediated_composition(mediated: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(mediated, dict):
        return ["mediated_composition must be an object"]

    required = {
        "claimed_level", "participants", "continuity", "channel", "intentionality",
        "directional_rates", "permitted_scopes", "fidelity", "local_admissibility",
        "null_models", "adaptation_evidence", "controls", "collective_agency_claim",
    }
    missing = sorted(required - mediated.keys())
    if missing:
        errors.append(f"mediated_composition missing fields: {', '.join(missing)}")
        return errors

    claimed = mediated.get("claimed_level")
    if claimed not in LEVEL_RANK:
        errors.append("mediated_composition.claimed_level is invalid")
        return errors

    participants = mediated.get("participants")
    if not isinstance(participants, list) or len(participants) < 3:
        errors.append("mediated_composition.participants requires at least three participants")
        participant_ids: set[str] = set()
    else:
        participant_ids = {item.get("participant_id") for item in participants if isinstance(item, dict) and item.get("participant_id")}
        roles = {item.get("role") for item in participants if isinstance(item, dict)}
        if not {"source", "intermediary", "destination"}.issubset(roles):
            errors.append("mediated_composition.participants must include source, intermediary, and destination roles")
        if len(participant_ids) != len(participants):
            errors.append("mediated_composition participant IDs must be present and unique")

    channel = mediated.get("channel")
    if not isinstance(channel, dict) or not isinstance(channel.get("stateful_intermediary"), bool) or not channel.get("observations"):
        errors.append("mediated_composition.channel requires stateful_intermediary and observations")

    intentionality = mediated.get("intentionality")
    if not isinstance(intentionality, dict):
        errors.append("mediated_composition.intentionality must be an object")
    elif participant_ids and not participant_ids.issubset(intentionality.keys()):
        errors.append("mediated_composition.intentionality must classify every participant")

    continuity = mediated.get("continuity")
    if not isinstance(continuity, list):
        errors.append("mediated_composition.continuity must be an array")
    elif participant_ids and {item.get("participant_id") for item in continuity if isinstance(item, dict)} != participant_ids:
        errors.append("mediated_composition.continuity must cover every participant exactly once")

    scopes = mediated.get("permitted_scopes")
    if not isinstance(scopes, list):
        errors.append("mediated_composition.permitted_scopes must be an array")
    elif participant_ids and {item.get("participant_id") for item in scopes if isinstance(item, dict)} != participant_ids:
        errors.append("mediated_composition.permitted_scopes must cover every participant exactly once")

    rates = mediated.get("directional_rates")
    if not isinstance(rates, list) or len(rates) < 2:
        errors.append("mediated_composition.directional_rates requires at least two directional records")
    else:
        for rate in rates:
            if not isinstance(rate, dict):
                errors.append("directional rate entries must be objects")
                continue
            if participant_ids and (rate.get("from") not in participant_ids or rate.get("to") not in participant_ids):
                errors.append("directional rate endpoints must reference declared participants")
            observed, limit = rate.get("observed"), rate.get("limit")
            if not isinstance(observed, (int, float)) or not isinstance(limit, (int, float)) or observed < 0 or limit < 0:
                errors.append("directional rates must use nonnegative numeric observed and limit values")
            elif observed > limit:
                errors.append("directional observed rate may not exceed its declared limit")

    fidelity = mediated.get("fidelity")
    if not isinstance(fidelity, dict):
        errors.append("mediated_composition.fidelity must be an object")
    else:
        for key in ("symbolic", "semantic", "pragmatic", "causal", "governance"):
            value = fidelity.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"mediated_composition.fidelity.{key} must be between 0 and 1")
        if not fidelity.get("evidence"):
            errors.append("mediated_composition.fidelity requires evidence")

    local = mediated.get("local_admissibility")
    if not isinstance(local, list):
        errors.append("mediated_composition.local_admissibility must be an array")
    elif participant_ids and {item.get("participant_id") for item in local if isinstance(item, dict)} != participant_ids:
        errors.append("mediated_composition.local_admissibility must cover every participant exactly once")

    controls = mediated.get("controls")
    if not isinstance(controls, dict):
        errors.append("mediated_composition.controls must be an object")
    else:
        missing_controls = sorted(REQUIRED_CONTROLS - controls.keys())
        if missing_controls:
            errors.append(f"mediated_composition.controls missing: {', '.join(missing_controls)}")
        for name in REQUIRED_CONTROLS & controls.keys():
            if not isinstance(controls[name], bool):
                errors.append(f"mediated_composition.controls.{name} must be boolean")

    null_models = mediated.get("null_models")
    if not isinstance(null_models, list) or not null_models:
        errors.append("mediated_composition.null_models requires at least one control")

    if not isinstance(mediated.get("collective_agency_claim"), bool):
        errors.append("mediated_composition.collective_agency_claim must be boolean")

    if not errors:
        supported = supported_mediated_level(mediated)
        if LEVEL_RANK[claimed] > LEVEL_RANK[supported]:
            errors.append(f"unsupported mediated escalation: claimed {claimed}, evidence supports {supported}")
        if claimed == "collective_agency" and not mediated.get("collective_agency_claim"):
            errors.append("collective_agency claimed_level requires collective_agency_claim=true")
        if mediated.get("collective_agency_claim"):
            agency = mediated.get("joint_agency_evidence")
            if not isinstance(agency, dict) or not all(agency.get(field) is True for field in JOINT_AGENCY_FIELDS):
                errors.append("collective agency requires complete joint-agency evidence; coupling alone is insufficient")
    return errors


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

    mediated = record.get("mediated_composition")
    if mediated:
        mediated_errors = validate_mediated_composition(mediated)
        if any("collective agency" in error or "unsupported mediated escalation" in error for error in mediated_errors):
            return "FAIL"
        if mediated_errors:
            return "INDETERMINATE"
        local = mediated.get("local_admissibility", [])
        decisions = {item.get("decision") for item in local if isinstance(item, dict)}
        if "deny" in decisions:
            return "FAIL"
        if decisions & {"quarantine", "defer"}:
            return "INDETERMINATE"

    if "INDETERMINATE" in statuses:
        return "INDETERMINATE"
    if "FAIL" in statuses or "PARTIAL" in statuses:
        return "PARTIAL"
    return "PASS"


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"assessment_id", "trace_id", "timestamp", "tests", "review", "overall_outcome", "error_attribution"}
    missing = sorted(required - record.keys())
    if missing:
        return [f"missing required fields: {', '.join(missing)}"]

    tests = record.get("tests")
    if not isinstance(tests, dict):
        return ["tests must be an object"]
    missing_tests = sorted(REQUIRED_TESTS - tests.keys())
    extra_tests = sorted(tests.keys() - REQUIRED_TESTS)
    if missing_tests:
        errors.append(f"missing tests: {', '.join(missing_tests)}")
    if extra_tests:
        errors.append(f"unknown tests: {', '.join(extra_tests)}")

    for name, result in tests.items():
        if not isinstance(result, dict):
            errors.append(f"{name}: result must be an object")
            continue
        for field in ("status", "score", "critical", "evidence"):
            if field not in result:
                errors.append(f"{name}: missing {field}")
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

    if "mediated_composition" in record:
        errors.extend(validate_mediated_composition(record["mediated_composition"]))

    outcome = record.get("overall_outcome")
    if outcome not in VALID_OUTCOMES:
        errors.append("invalid overall_outcome")

    attributions = record.get("error_attribution")
    if not isinstance(attributions, list):
        errors.append("error_attribution must be an array")
    else:
        invalid = sorted(set(attributions) - VALID_ATTRIBUTIONS)
        if invalid:
            errors.append(f"invalid error attribution: {', '.join(invalid)}")

    structural_errors = [error for error in errors if not error.startswith("unsupported mediated escalation")]
    if not structural_errors:
        expected = recommended_outcome(record)
        if outcome != expected:
            errors.append(f"overall_outcome must be {expected}, got {outcome}")
    return errors


def validate_jsonl(path: Path) -> int:
    failures = 0
    records = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            records += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                failures += 1
                print(f"{path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                continue
            errors = validate_record(record)
            if errors:
                failures += 1
                for error in errors:
                    print(f"{path}:{line_number}: {error}", file=sys.stderr)

    if records == 0:
        print(f"{path}: no records found", file=sys.stderr)
        return 1
    if failures:
        print(f"FAIL: {failures}/{records} records invalid", file=sys.stderr)
        return 1
    print(f"PASS: {records} records valid")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="JSONL assessment file")
    args = parser.parse_args()
    return validate_jsonl(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
