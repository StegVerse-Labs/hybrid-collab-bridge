"""Tests for commit-time governance snapshot integrity and BCAT/GCAT replay."""
from __future__ import annotations

import copy
import sys
import types
from pathlib import Path

from api.app.governance.governance_snapshot import (
    build_governance_snapshot,
    regenerate_bcat_gcat,
    verify_snapshot_integrity,
)


def _install_fake_cge_policy(monkeypatch):
    cge = types.ModuleType("cge")
    policy = types.ModuleType("cge.policy")

    def evaluate_bcat(value):
        payload = value.get("payload", {})
        return {
            "observability": payload.get("observability", 0.8),
            "context_stability": 0.8,
            "authority_clarity": 0.8,
            "reversibility_margin": 0.8,
            "risk": payload.get("risk", 0.2),
        }

    def evaluate_gcat(bcat):
        return {"coherence": round(1.0 - bcat["risk"], 3)}

    policy.evaluate_bcat = evaluate_bcat
    policy.evaluate_gcat = evaluate_gcat
    cge.policy = policy
    monkeypatch.setitem(sys.modules, "cge", cge)
    monkeypatch.setitem(sys.modules, "cge.policy", policy)


def _snapshot():
    evaluation_input = {
        "type": "ingest",
        "source": "test",
        "actor": {"entity_id": "assessor"},
        "payload": {"observability": 0.9, "risk": 0.1},
        "timestamp": 1,
        "ingest_id": "fixed-id",
    }
    bcat = {
        "observability": 0.9,
        "context_stability": 0.8,
        "authority_clarity": 0.8,
        "reversibility_margin": 0.8,
        "risk": 0.1,
    }
    gcat = {"coherence": 0.9}
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
    return build_governance_snapshot(
        proposal={"assessment_hash": "abc"},
        actor={"entity_id": "assessor"},
        source="test",
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


def test_snapshot_integrity_and_regeneration(monkeypatch):
    _install_fake_cge_policy(monkeypatch)
    snapshot = _snapshot()
    assert verify_snapshot_integrity(snapshot)["verified"] is True
    replay = regenerate_bcat_gcat(snapshot)
    assert replay["verified"] is True
    assert replay["checks"]["evaluator_source_verified"] is True
    assert replay["regenerated"]["canonical_decision"] == "allow"


def test_snapshot_tamper_is_detected(monkeypatch):
    _install_fake_cge_policy(monkeypatch)
    snapshot = copy.deepcopy(_snapshot())
    snapshot["evaluation_input"]["payload"]["risk"] = 0.95
    replay = regenerate_bcat_gcat(snapshot)
    assert replay["verified"] is False
    assert replay["checks"]["snapshot_hash_verified"] is False
    assert replay["checks"]["evaluation_input_hash_verified"] is False


def test_policy_threshold_tamper_is_detected(monkeypatch):
    _install_fake_cge_policy(monkeypatch)
    snapshot = copy.deepcopy(_snapshot())
    snapshot["threshold_profile"]["risk_max"] = 0.05
    replay = regenerate_bcat_gcat(snapshot)
    assert replay["verified"] is False
    assert replay["checks"]["snapshot_hash_verified"] is False
    assert replay["checks"]["admissibility_regenerated"] is False


def test_evaluator_source_evidence_tamper_is_detected(monkeypatch):
    _install_fake_cge_policy(monkeypatch)
    snapshot = copy.deepcopy(_snapshot())
    snapshot["evaluator_source"]["evaluate_bcat"]["source_hash"] = "0" * 64
    replay = regenerate_bcat_gcat(snapshot)
    assert replay["verified"] is False
    assert replay["checks"]["snapshot_hash_verified"] is False
    assert replay["checks"]["evaluator_source_hash_verified"] is False
    assert replay["checks"]["evaluator_source_verified"] is False
