"""Tests for deterministic Human–LLM replay and independent verification."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

from api.app.governance.governance_snapshot import build_governance_snapshot
from api.app.governance.human_llm_evidence import (
    persist_mediated_receipts,
    sha256_json,
)
from api.app.governance.human_llm_replay import replay_assessment
from api.app.governance.receipt_signing import ReceiptSigner


def _install_fake_cge_policy(monkeypatch) -> None:
    cge = types.ModuleType("cge")
    policy = types.ModuleType("cge.policy")

    def evaluate_bcat(value):
        payload = value.get("payload", {})
        return {
            "observability": payload.get("observability", 0.9),
            "context_stability": 0.8,
            "authority_clarity": 0.8,
            "reversibility_margin": 0.8,
            "risk": payload.get("risk", 0.1),
        }

    def evaluate_gcat(bcat):
        return {"coherence": round(1.0 - bcat["risk"], 3)}

    policy.evaluate_bcat = evaluate_bcat
    policy.evaluate_gcat = evaluate_gcat
    cge.policy = policy
    monkeypatch.setitem(sys.modules, "cge", cge)
    monkeypatch.setitem(sys.modules, "cge.policy", policy)


def assessment_record() -> dict:
    names = {
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
    return {
        "assessment_id": "replay-001",
        "trace_id": "trace-replay-001",
        "timestamp": "2026-07-24T18:00:00Z",
        "claim_consequence": "low",
        "tests": {
            name: {"status": "PASS", "score": 1.0, "critical": False, "evidence": [name]}
            for name in names
        },
        "review": {
            "human_present": True,
            "comprehension_demonstrated": True,
            "objections_considered": True,
        },
        "overall_outcome": "PASS",
        "error_attribution": [],
    }


def _persist_governance_snapshot(
    session_dir: Path,
    assessment: dict,
    monkeypatch,
) -> tuple[dict, dict]:
    _install_fake_cge_policy(monkeypatch)
    from cge.policy import evaluate_bcat, evaluate_gcat

    evaluation_input = {
        "type": "ingest",
        "source": "human-llm-replay-test",
        "actor": {"entity_id": "assessor"},
        "payload": {"observability": 0.9, "risk": 0.1},
        "timestamp": 1,
        "ingest_id": "fixed-replay-id",
    }
    bcat = evaluate_bcat(evaluation_input)
    gcat = evaluate_gcat(bcat)
    constitution = {
        "threshold_profiles": {
            "standard": {
                "observability_min": 0.6,
                "context_stability_min": 0.5,
                "authority_clarity_min": 0.5,
                "reversibility_margin_min": 0.3,
                "risk_max": 0.7,
            }
        }
    }
    snapshot = build_governance_snapshot(
        proposal={"assessment_hash": sha256_json(assessment)},
        actor={"entity_id": "assessor"},
        source="human-llm-replay-test",
        constitution=constitution,
        ingest_result={
            "evaluation_input": evaluation_input,
            "evaluator": {"mode": "embedded"},
            "bcat": bcat,
            "gcat": gcat,
            "admissible": True,
        },
        canonical_decision="allow",
        cge_path=Path("/tmp/cge"),
    )
    (session_dir / "08_commit_time_governance_snapshot.json").write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )
    return bcat, gcat


def write_artifact(
    session_dir: Path,
    assessment: dict,
    monkeypatch,
    decision: str = "allow",
) -> None:
    bcat, gcat = _persist_governance_snapshot(session_dir, assessment, monkeypatch)
    artifact = {
        "assessment": assessment,
        "admission": {
            "decision": decision,
            "structural_decision": "allow",
            "canonical_decision": "allow",
            "publication_allowed": decision == "allow",
            "errors": [],
            "reasoning": [],
            "bcat": bcat,
            "gcat": gcat,
        },
        "mediated_receipts": None,
        "receipt": {"verified": True},
    }
    (session_dir / "04_human_llm_pair_assessment.json").write_text(
        json.dumps(artifact, indent=2), encoding="utf-8"
    )


def test_pair_replay_is_identical(tmp_path: Path, monkeypatch):
    write_artifact(tmp_path, assessment_record(), monkeypatch)
    result = replay_assessment(tmp_path, "replay-001")
    assert result["replay_status"] == "IDENTICAL"
    assert result["reconstructable"] is True
    assert result["checks"]["schema_verified"] is True
    assert result["checks"]["governance_snapshot_verified"] is True
    assert result["checks"]["canonical_decision_regenerated"] is True
    assert Path(result["replay_artifact"]).exists()


def test_replay_detects_stored_decision_tampering(tmp_path: Path, monkeypatch):
    write_artifact(tmp_path, assessment_record(), monkeypatch, decision="deny")
    result = replay_assessment(tmp_path, "replay-001")
    assert result["replay_status"] == "MISMATCH"
    assert result["checks"]["canonical_decision_regenerated"] is True
    assert result["checks"]["final_decision_verified"] is False


def test_replay_detects_assessment_outcome_tampering(tmp_path: Path, monkeypatch):
    record = assessment_record()
    record["overall_outcome"] = "PARTIAL"
    write_artifact(tmp_path, record, monkeypatch)
    result = replay_assessment(tmp_path, "replay-001")
    assert result["replay_status"] == "MISMATCH"
    assert result["checks"]["outcome_verified"] is False


def test_mediated_replay_verifies_authenticated_chain(tmp_path: Path, monkeypatch):
    record = assessment_record()
    record["mediated_composition"] = {
        "claimed_level": "governed_composition",
        "participants": [
            {"participant_id": "model-a", "participant_type": "model", "role": "source"},
            {"participant_id": "human-h", "participant_type": "human", "role": "intermediary"},
            {"participant_id": "model-b", "participant_type": "model", "role": "destination"},
        ],
        "continuity": [
            {"participant_id": value, "status": "verified", "evidence": ["continuity"]}
            for value in ("model-a", "human-h", "model-b")
        ],
        "channel": {
            "medium_state": "developing",
            "observations": ["relay observed"],
            "stateful_intermediary": True,
        },
        "intentionality": {
            "model-a": "unknown",
            "human-h": "deliberate",
            "model-b": "unknown",
        },
        "directional_rates": [
            {"from": "model-a", "to": "human-h", "unit": "messages_per_minute", "observed": 1, "limit": 5},
            {"from": "human-h", "to": "model-b", "unit": "messages_per_minute", "observed": 1, "limit": 5},
        ],
        "permitted_scopes": [
            {
                "participant_id": value,
                "observe": ["text"],
                "express": ["text"],
                "interpret": ["text"],
                "execute": [],
            }
            for value in ("model-a", "human-h", "model-b")
        ],
        "fidelity": {
            "symbolic": 0.9,
            "semantic": 0.9,
            "pragmatic": 0.9,
            "causal": 0.9,
            "governance": 0.9,
            "evidence": ["reconstruction"],
        },
        "local_admissibility": [
            {
                "participant_id": value,
                "decision": "allow",
                "policy_ref": f"policy:{value}",
                "evidence": ["admitted"],
                "receipt_ref": f"receipt:{value}",
            }
            for value in ("model-a", "human-h", "model-b")
        ],
        "null_models": [
            {
                "name": "generic_language",
                "tested": True,
                "result": "rejected",
                "evidence": ["control"],
            }
        ],
        "adaptation_evidence": ["adaptation"],
        "controls": {
            "paraphrase": True,
            "intermediary_substitution": True,
            "relay_delay": True,
            "hidden_provenance": True,
            "adversarial_relay": True,
            "independent_convergence": True,
        },
        "collective_agency_claim": False,
    }
    signer = ReceiptSigner("replay-signer", "test:key:1", b"replay-secret")
    reference = persist_mediated_receipts(record, tmp_path, signer=signer)
    assert reference is not None

    bcat, gcat = _persist_governance_snapshot(tmp_path, record, monkeypatch)
    artifact = {
        "assessment": record,
        "admission": {
            "decision": "allow",
            "structural_decision": "allow",
            "canonical_decision": "allow",
            "publication_allowed": True,
            "errors": [],
            "reasoning": [],
            "bcat": bcat,
            "gcat": gcat,
        },
        "mediated_receipts": reference,
        "receipt": {"verified": True},
    }
    (tmp_path / "04_human_llm_pair_assessment.json").write_text(
        json.dumps(artifact, indent=2), encoding="utf-8"
    )

    import os

    previous = {
        "HCB_RECEIPT_SIGNING_KEY": os.environ.get("HCB_RECEIPT_SIGNING_KEY"),
        "HCB_RECEIPT_SIGNER_ID": os.environ.get("HCB_RECEIPT_SIGNER_ID"),
        "HCB_RECEIPT_SIGNING_KEY_REF": os.environ.get("HCB_RECEIPT_SIGNING_KEY_REF"),
    }
    os.environ["HCB_RECEIPT_SIGNING_KEY"] = "replay-secret"
    os.environ["HCB_RECEIPT_SIGNER_ID"] = "replay-signer"
    os.environ["HCB_RECEIPT_SIGNING_KEY_REF"] = "test:key:1"
    try:
        result = replay_assessment(tmp_path, "replay-001")
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert result["replay_status"] == "IDENTICAL"
    assert result["checks"]["receipt_chain_verified"] is True
    assert result["checks"]["governance_snapshot_verified"] is True


def test_mediated_replay_detects_receipt_tampering(tmp_path: Path, monkeypatch):
    record = assessment_record()
    record["mediated_composition"] = {"local_admissibility": []}
    write_artifact(tmp_path, record, monkeypatch)
    result = replay_assessment(tmp_path, "replay-001")
    assert result["replay_status"] == "MISMATCH"
    assert result["checks"]["receipt_chain_verified"] is False
