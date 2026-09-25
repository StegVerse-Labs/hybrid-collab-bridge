"""Synthetic common-goal mutual-adaptation assessment for the existing pair evaluator.

This is a source-level quality assessment, never an execution/admission authority.
No physiology, nonhuman welfare, consent, or Master Records truth is inferred.
"""
from __future__ import annotations

from typing import Any

TEST_NAMES = (
    "common_goal_compatibility",
    "changing_capacity",
    "observed_adaptation",
    "independent_agency",
    "participant_viability",
    "provenance_integrity",
    "reconstruction",
)


def _number(value: Any) -> bool:
    return type(value) in (int, float) and 0 <= value <= 1


def evaluate_common_goal_adaptation(data: Any) -> dict[str, Any]:
    """Return all seven bounded checks and an explicit source-only disposition."""
    errors: list[str] = []
    results = {name: "INDETERMINATE" for name in TEST_NAMES}
    if not isinstance(data, dict):
        return {"tests": results, "disposition": "INDETERMINATE", "errors": ["common_goal_adaptation must be an object"]}
    if data.get("mode") != "synthetic":
        errors.append("only synthetic evaluation is supported; consequential deployment requires existing owner review")
    participants = data.get("participants")
    if not isinstance(participants, list) or len(participants) < 2 or not all(isinstance(p, dict) for p in participants):
        errors.append("at least two independent participant records are required")
        return {"tests": results, "disposition": "INDETERMINATE", "errors": errors}
    ids = [p.get("participant_id") for p in participants]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        errors.append("participant IDs must be nonempty and unique")
    for p in participants:
        if p.get("goal_source") not in {"declared", "independently_verified", "unexpressed"}:
            errors.append("each goal requires attributable origin; unsupported inference is forbidden")
        if not isinstance(p.get("goals"), list) or not all(isinstance(g, str) and g for g in p.get("goals", [])):
            errors.append("each participant must have an explicit goal list")
    if errors:
        return {"tests": results, "disposition": "INDETERMINATE", "errors": errors}
    sourced = [p for p in participants if p["goal_source"] != "unexpressed"]
    common = set.intersection(*(set(p["goals"]) for p in sourced)) if len(sourced) == len(participants) else set()
    chosen = data.get("selected_goal")
    selected = isinstance(chosen, str) and chosen in common
    if common:
        results["common_goal_compatibility"] = "PASS" if selected else "FAIL"
    else:
        results["common_goal_compatibility"] = "PASS" if chosen is None else "FAIL"
    if not all(_number(p.get(k)) for p in participants for k in
               ("capacity_before", "capacity_after", "handoff_after", "success_before",
                "success_after", "heldout_success", "fixed_control_success", "no_feedback_success")):
        errors.append("capacity, handoff, success and control measures must be independently numeric in [0,1]")
    if not all(type(p.get(k)) is int and p[k] >= 0 for p in participants for k in
               ("clarifications_before", "clarifications_after")):
        errors.append("clarification counts must be nonnegative integers")
    if not all(_number(data.get(k)) for k in ("minimum_handoff", "minimum_gain", "minimum_heldout")):
        errors.append("pre-registered thresholds must be in [0,1]")
    cap_changed = any(_number(p.get("capacity_after")) and _number(p.get("capacity_before"))
                      and p["capacity_after"] < p["capacity_before"] for p in participants)
    bound = data.get("maximum_clarification_increase")
    if type(bound) is not int or bound < 0:
        errors.append("maximum clarification increase must be a nonnegative integer")
    if not errors:
        results["changing_capacity"] = "PASS" if (
            cap_changed and all(p["handoff_after"] >= data["minimum_handoff"] and
                                p["clarifications_after"] - p["clarifications_before"] <= bound
                                for p in participants)
        ) else "FAIL"
        gains = [p["success_after"] - max(p["fixed_control_success"], p["no_feedback_success"])
                 for p in participants]
        results["observed_adaptation"] = "PASS" if (
            any(g >= data["minimum_gain"] and g > 0 for g in gains) and
            all(p["success_after"] >= p["success_before"] and
                p["heldout_success"] >= data["minimum_heldout"] for p in participants)
        ) else "FAIL"
    revoked = [p for p in participants if p.get("revoked") is True]
    agency_typed = all(type(p.get("consent")) is bool and type(p.get("revoked")) is bool and
                       type(p.get("attempted_after_revocation")) is bool and
                       p.get("revocation_disposition") in {"DENY", "DEFER", "NOT_APPLICABLE"}
                       for p in participants)
    if agency_typed:
        # Independent post-withdrawal recomputation: a revoked participant's
        # previous goal cannot be carried forward merely because a fixture
        # asserts that the goal was recomputed.
        eligible = [p for p in participants if p["consent"] and not p["revoked"]
                    and p["goal_source"] != "unexpressed"]
        post_common = (set.intersection(*(set(p["goals"]) for p in eligible))
                       if len(eligible) >= 2 else set())
        post_selected = data.get("selected_goal_after_revocation")
        post_goal_valid = (isinstance(post_selected, str) and bool(post_selected)
                           and post_selected in post_common) if post_common else post_selected is None
        results["independent_agency"] = "PASS" if (
            revoked and all(not p["attempted_after_revocation"] and
                            p["revocation_disposition"] in {"DENY", "DEFER"} for p in revoked)
            and all(p["consent"] or p["revoked"] for p in participants)
            and data.get("goal_recomputed_after_revocation") is True
            and "selected_goal_after_revocation" in data and post_goal_valid
        ) else "FAIL"
    else:
        errors.append("consent, revocation and post-revocation attempt/disposition are required")
    if all(type(p.get("viability_ok")) is bool for p in participants):
        results["participant_viability"] = "PASS" if all(p["viability_ok"] for p in participants) else "FAIL"
    else:
        errors.append("per-participant viability observations are required")
    if all(type(data.get(k)) is bool for k in
           ("vocabulary_collision_injected", "vocabulary_collision_detected",
            "false_shared_goal_injected", "false_shared_goal_flagged")):
        results["provenance_integrity"] = "PASS" if all(data[k] for k in
            ("vocabulary_collision_injected", "vocabulary_collision_detected",
             "false_shared_goal_injected", "false_shared_goal_flagged")) else "FAIL"
    else:
        errors.append("provenance and vocabulary negative controls must be explicit")
    refs = data.get("local_receipts")
    if isinstance(refs, list) and {r.get("participant_id") for r in refs if isinstance(r, dict)} == set(ids) and len(refs) == len(ids):
        results["reconstruction"] = "PASS" if (
            data.get("fixture_replay_pass") is True and all(
                isinstance(r.get("receipt_ref"), str) and r["receipt_ref"] and
                isinstance(r.get("predecessor_hash"), str) and r["predecessor_hash"]
                for r in refs)
        ) else "FAIL"
    else:
        errors.append("exact participant coverage in local synthetic receipt references required")
    disposition = ("INDETERMINATE" if errors or any(x == "INDETERMINATE" for x in results.values())
                   else "PASS" if all(x == "PASS" for x in results.values()) else "FAIL")
    return {"tests": results, "disposition": disposition, "errors": errors}
