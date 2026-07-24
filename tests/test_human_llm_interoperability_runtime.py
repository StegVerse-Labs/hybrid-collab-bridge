"""Runtime tests for governed Human–LLM pair assessments."""
from __future__ import annotations

import json
from pathlib import Path

from api.app.governance import human_llm_interoperability as runtime


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
    errors = runtime.validate_assessment(record)
    assert errors == ["overall_outcome must be FAIL, got PASS"]


def test_receipt_is_hash_chained(tmp_path: Path):
    runtime.CGE_PATH = tmp_path / "cge"
    first = runtime._append_receipt({
        "trace_id": "trace-1",
        "assessment_id": "a-1",
        "outcome": "PASS",
    }, "allow")
    second = runtime._append_receipt({
        "trace_id": "trace-1",
        "assessment_id": "a-2",
        "outcome": "FAIL",
    }, "deny")
    assert first["previous_hash"] == "GENESIS"
    assert second["previous_hash"] == first["entry_hash"]
    ledger = (runtime.CGE_PATH / "state" / "ledger.jsonl").read_text().splitlines()
    assert len(ledger) == 2
    assert json.loads(ledger[-1])["entry_hash"] == second["entry_hash"]


def test_session_path_cannot_escape_root(tmp_path: Path):
    runtime.SESSIONS_ROOT = tmp_path / "sessions"
    runtime.SESSIONS_ROOT.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        runtime._resolve_session(str(outside))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("path escape was accepted")
