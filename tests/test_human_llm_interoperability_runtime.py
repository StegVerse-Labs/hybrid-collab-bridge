"""Runtime tests for governed Human–LLM pair assessments."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from api.app.governance import human_llm_interoperability as runtime
from api.app.governance.entity import EntityIdentity


def assessment(outcome: str = "PASS", consequence: str = "low", comprehension: bool = True):
    tests = {
        name: {
            "status": "PASS",
            "score": 1.0,
            "critical": name in {
                "meaning_preservation",
                "boundary_control",
                "audit_gap_control",
                "review_comprehension",
            },
            "evidence": [f"evidence:{name}"],
        }
        for name in runtime.REQUIRED_TESTS
    }
    return {
        "assessment_id": "assessment-runtime-001",
        "trace_id": "trace-runtime-001",
        "timestamp": "2026-07-23T00:00:00Z",
        "claim_consequence": consequence,
        "tests": tests,
        "review": {
            "human_present": True,
            "comprehension_demonstrated": comprehension,
            "objections_considered": True,
        },
        "overall_outcome": outcome,
        "error_attribution": [],
    }


class FakeGate:
    def __init__(self, decision: str = "allow"):
        self.decision = decision
        self.calls = []

    async def admit_proposal(self, proposal, actor, source):
        self.calls.append({"proposal": proposal, "actor": actor, "source": source})
        return SimpleNamespace(
            decision=self.decision,
            receipt={
                "receipt_id": "receipt-1",
                "ledger_entry_id": "entry-1",
                "entry_hash": "hash-1",
                "verified": True,
            },
            bcat={"observability": 1.0, "risk": 0.0},
            gcat={"g": 0.25, "c": 0.25, "a": 0.25, "t": 0.25},
            reasoning="canonical test gate",
        )


def configure_fake(tmp_path: Path, decision: str = "allow") -> FakeGate:
    gate = FakeGate(decision)
    runtime.SESSIONS_ROOT = tmp_path / "sessions"
    runtime.SESSIONS_ROOT.mkdir(parents=True)
    runtime.CGE_PATH = tmp_path / "cge"
    runtime.ADMISSION_GATE = gate
    runtime.ASSESSOR_ENTITY = EntityIdentity(
        entity_id="test-assessor",
        entity_type="automated_process",
        org_id="StegVerse-Labs",
        owner_human="test",
    )
    return gate


def test_pass_record_is_valid():
    assert runtime.validate_assessment(assessment()) == []


def test_critical_failure_forces_fail():
    record = assessment(outcome="FAIL")
    record["tests"]["meaning_preservation"]["status"] = "FAIL"
    record["tests"]["meaning_preservation"]["score"] = 0.0
    assert runtime.validate_assessment(record) == []


def test_high_consequence_requires_demonstrated_comprehension():
    record = assessment(outcome="FAIL", consequence="critical", comprehension=False)
    assert runtime.validate_assessment(record) == []


def test_score_cannot_override_critical_failure():
    record = assessment(outcome="PASS")
    record["tests"]["audit_gap_control"]["status"] = "FAIL"
    record["tests"]["audit_gap_control"]["score"] = 0.99
    assert runtime.validate_assessment(record) == ["overall_outcome must be FAIL, got PASS"]


def test_governed_pass_writes_session_artifact(tmp_path: Path):
    gate = configure_fake(tmp_path)
    session = runtime.SESSIONS_ROOT / "2026-07-23" / "pair-test"
    session.mkdir(parents=True)
    result = asyncio.run(runtime.govern_assessment(assessment(), session))
    assert result.admission_decision == "allow"
    assert result.publication_allowed is True
    assert gate.calls[0]["source"] == "hybrid-collab-bridge/human-llm-interoperability"
    artifact = json.loads((session / "04_human_llm_pair_assessment.json").read_text())
    assert artifact["receipt"]["verified"] is True
    assert artifact["admission"]["canonical_decision"] == "allow"


def test_structural_failure_cannot_be_overridden_by_gate(tmp_path: Path):
    configure_fake(tmp_path, decision="allow")
    session = runtime.SESSIONS_ROOT / "2026-07-23" / "pair-fail"
    session.mkdir(parents=True)
    record = assessment(outcome="FAIL")
    record["tests"]["boundary_control"]["status"] = "FAIL"
    record["tests"]["boundary_control"]["score"] = 0.0
    result = asyncio.run(runtime.govern_assessment(record, session))
    assert result.admission_decision == "deny"
    assert result.publication_allowed is False


def test_canonical_denial_overrides_structural_pass(tmp_path: Path):
    configure_fake(tmp_path, decision="deny")
    session = runtime.SESSIONS_ROOT / "2026-07-23" / "pair-gate-deny"
    session.mkdir(parents=True)
    result = asyncio.run(runtime.govern_assessment(assessment(), session))
    assert result.admission_decision == "deny"
    assert result.publication_allowed is False


def test_session_path_cannot_escape_root(tmp_path: Path):
    configure_fake(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        runtime._resolve_session(str(outside))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("path escape was accepted")
