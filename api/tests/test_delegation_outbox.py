"""Tests for session-trace to delegation-outbox reconciliation."""
import json
from pathlib import Path

from scripts.reconcile_delegation_outbox import reconcile


def _trace(status="OK", integrity_decision="ALLOW_NEXT_BOUNDARY"):
    return {
        "transition_id": "transition-001",
        "chain_id": "run-001",
        "receipt": {
            "receipt_id": "receipt-bridge-001",
            "ledger_entry_id": "event-001",
            "payload": {"origin_manifest_id": "manifest-001"},
        },
        "integrity": {
            "decision": integrity_decision,
            "content_sha256": "a" * 64,
            "required_sections": ["Purpose"],
            "missing_sections": [],
            "empty": False,
            "reasoning": "complete",
            "passed": integrity_decision == "ALLOW_NEXT_BOUNDARY",
        },
        "run_boundary": {
            "status": status,
            "may_ingest_accepted_result": status == "OK",
            "preserve_governance_event": True,
            "requires_human": False,
            "reasoning": "bounded",
        },
        "integrity_event_receipt": {"receipt_id": "receipt-integrity-001"},
    }


def test_reconcile_emits_deterministic_candidate_and_state(tmp_path):
    sessions = tmp_path / "sessions" / "2026-07-14" / "run-one"
    sessions.mkdir(parents=True)
    (sessions / "03_referee.json").write_text(json.dumps(_trace()), encoding="utf-8")
    outbox = tmp_path / "outbox"
    state_path = tmp_path / "state.json"

    state = reconcile(tmp_path / "sessions", outbox, state_path)
    assert state["processed_count"] == 1
    assert state["skipped_count"] == 0
    assert state["manual_action_required"] is False
    records = list(outbox.glob("*.json"))
    assert len(records) == 1
    candidate = json.loads(records[0].read_text(encoding="utf-8"))
    assert candidate["transition_id"] == "transition-001"
    assert candidate["run_id"] == "run-001"
    assert candidate["target_repository"] == "StegVerse-Labs/Ecosystem-Delegation"
    assert candidate["lifecycle_status"] == "READY"
    assert candidate["delegation_authority"] is False


def test_failed_integrity_candidate_is_emitted_fail_closed(tmp_path):
    sessions = tmp_path / "sessions" / "2026-07-14" / "run-two"
    sessions.mkdir(parents=True)
    (sessions / "03_referee.json").write_text(
        json.dumps(_trace("INTEGRITY_FAILED", "FAIL_CLOSED")), encoding="utf-8"
    )
    outbox = tmp_path / "outbox"
    state = reconcile(tmp_path / "sessions", outbox, tmp_path / "state.json")
    assert state["processed_count"] == 1
    candidate = json.loads(next(outbox.glob("*.json")).read_text(encoding="utf-8"))
    assert candidate["lifecycle_status"] == "FAIL_CLOSED"
    assert candidate["admissibility_result"] == "PENDING"


def test_invalid_trace_is_recorded_without_manual_task(tmp_path):
    sessions = tmp_path / "sessions" / "bad"
    sessions.mkdir(parents=True)
    (sessions / "03_referee.json").write_text("not-json", encoding="utf-8")
    state = reconcile(tmp_path / "sessions", tmp_path / "outbox", tmp_path / "state.json")
    assert state["processed_count"] == 0
    assert state["skipped_count"] == 1
    assert state["manual_action_required"] is False
