"""Commit-time governance snapshots for deterministic admission replay."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_governance_snapshot(
    *,
    proposal: dict[str, Any],
    actor: dict[str, Any],
    source: str,
    constitution: dict[str, Any],
    ingest_result: dict[str, Any],
    canonical_decision: str,
    cge_path: Path,
) -> dict[str, Any]:
    evaluation_input = ingest_result.get("evaluation_input")
    evaluator = ingest_result.get("evaluator", {})
    snapshot_body = {
        "snapshot_version": "1.0",
        "proposal": proposal,
        "proposal_hash": sha256_json(proposal),
        "actor": actor,
        "actor_hash": sha256_json(actor),
        "source": source,
        "constitution": constitution,
        "constitution_hash": sha256_json(constitution),
        "threshold_profile": constitution.get("threshold_profiles", {}).get("standard", {}),
        "evaluation_input": evaluation_input,
        "evaluation_input_hash": sha256_json(evaluation_input) if evaluation_input is not None else None,
        "evaluator": evaluator,
        "cge_path_ref": str(cge_path),
        "bcat": ingest_result.get("bcat", {}),
        "gcat": ingest_result.get("gcat", {}),
        "admissible": bool(ingest_result.get("admissible", False)),
        "canonical_decision": canonical_decision,
    }
    return {**snapshot_body, "snapshot_hash": sha256_json(snapshot_body)}


def verify_snapshot_integrity(snapshot: dict[str, Any]) -> dict[str, Any]:
    declared_hash = snapshot.get("snapshot_hash")
    body = {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
    checks = {
        "snapshot_hash_verified": declared_hash == sha256_json(body),
        "proposal_hash_verified": snapshot.get("proposal_hash") == sha256_json(snapshot.get("proposal")),
        "actor_hash_verified": snapshot.get("actor_hash") == sha256_json(snapshot.get("actor")),
        "constitution_hash_verified": snapshot.get("constitution_hash") == sha256_json(snapshot.get("constitution")),
        "evaluation_input_hash_verified": (
            snapshot.get("evaluation_input") is not None
            and snapshot.get("evaluation_input_hash") == sha256_json(snapshot.get("evaluation_input"))
        ),
    }
    return {"verified": all(checks.values()), "checks": checks}


def threshold_admissible(bcat: dict[str, Any], profile: dict[str, Any]) -> bool:
    checks = [
        bcat.get("observability", 0) >= profile.get("observability_min", 0.6),
        bcat.get("context_stability", 0) >= profile.get("context_stability_min", 0.5),
        bcat.get("authority_clarity", 0) >= profile.get("authority_clarity_min", 0.5),
        bcat.get("reversibility_margin", 0) >= profile.get("reversibility_margin_min", 0.3),
        bcat.get("risk", 1.0) <= profile.get("risk_max", 0.7),
    ]
    return all(checks)


def regenerate_bcat_gcat(snapshot: dict[str, Any]) -> dict[str, Any]:
    integrity = verify_snapshot_integrity(snapshot)
    errors: list[str] = []
    if not integrity["verified"]:
        errors.append("governance snapshot integrity verification failed")

    evaluation_input = snapshot.get("evaluation_input")
    evaluator = snapshot.get("evaluator", {})
    regenerated_bcat: dict[str, Any] | None = None
    regenerated_gcat: dict[str, Any] | None = None

    if not isinstance(evaluation_input, dict):
        errors.append("governance snapshot has no deterministic evaluation input")
    elif evaluator.get("mode") != "embedded":
        errors.append("independent evaluator regeneration is unavailable for this snapshot mode")
    else:
        cge_path = str(snapshot.get("cge_path_ref", ""))
        if cge_path and cge_path not in sys.path:
            sys.path.insert(0, cge_path)
        try:
            from cge.policy import evaluate_bcat, evaluate_gcat

            regenerated_bcat = evaluate_bcat(json.loads(json.dumps(evaluation_input)))
            regenerated_gcat = evaluate_gcat(regenerated_bcat)
        except Exception as exc:  # evaluator failures must remain explicit and fail closed
            errors.append(f"CGE evaluator regeneration failed: {exc}")

    stored_bcat = snapshot.get("bcat", {})
    stored_gcat = snapshot.get("gcat", {})
    bcat_verified = regenerated_bcat is not None and regenerated_bcat == stored_bcat
    gcat_verified = regenerated_gcat is not None and regenerated_gcat == stored_gcat
    profile = snapshot.get("threshold_profile", {})
    regenerated_admissible = (
        threshold_admissible(regenerated_bcat, profile) if regenerated_bcat is not None else None
    )
    admissibility_verified = regenerated_admissible == snapshot.get("admissible")
    regenerated_decision = "allow" if regenerated_admissible else "deny"
    decision_verified = regenerated_admissible is not None and regenerated_decision == snapshot.get("canonical_decision")

    checks = {
        **integrity["checks"],
        "bcat_regenerated": bcat_verified,
        "gcat_regenerated": gcat_verified,
        "admissibility_regenerated": admissibility_verified,
        "canonical_decision_regenerated": decision_verified,
    }
    for name, passed in checks.items():
        if not passed:
            errors.append(f"governance replay check failed: {name}")

    return {
        "verified": all(checks.values()),
        "checks": checks,
        "errors": list(dict.fromkeys(errors)),
        "stored": {
            "bcat": stored_bcat,
            "gcat": stored_gcat,
            "admissible": snapshot.get("admissible"),
            "canonical_decision": snapshot.get("canonical_decision"),
        },
        "regenerated": {
            "bcat": regenerated_bcat,
            "gcat": regenerated_gcat,
            "admissible": regenerated_admissible,
            "canonical_decision": regenerated_decision if regenerated_admissible is not None else None,
        },
    }
