"""Contract tests for autonomous bridge-to-delegation candidates."""
from app.governance.delegation_candidate import build_delegation_candidate


def _candidate(status: str = "OK"):
    return build_delegation_candidate(
        transition_id="transition-001",
        run_id="run-001",
        event_id="event-001",
        origin_manifest_id="manifest-001",
        bridge_status=status,
        content_sha256="a" * 64,
        integrity_decision="ALLOW_NEXT_BOUNDARY",
        evidence_refs=["receipt:bridge-1", "receipt:integrity-1", "receipt:bridge-1"],
        integrity_evidence_ref="receipt:integrity-1",
    )


def test_candidate_preserves_identity_and_targets_delegation_only():
    candidate = _candidate()
    assert candidate.transition_id == "transition-001"
    assert candidate.run_id == "run-001"
    assert candidate.event_id == "event-001"
    assert candidate.origin_manifest_id == "manifest-001"
    assert candidate.target_repository == "StegVerse-Labs/Ecosystem-Delegation"
    assert candidate.target_boundary == "delegation_intake"
    assert candidate.lifecycle_status == "READY"


def test_candidate_has_no_execution_or_delegation_authority():
    candidate = _candidate()
    assert candidate.execution_authority is False
    assert candidate.publication_authority is False
    assert candidate.delegation_authority is False
    assert candidate.admissibility_result == "PENDING"
    assert candidate.commit_time_validity == "PENDING"
    assert candidate.action_ref is None
    assert candidate.final_receipt_id is None


def test_evidence_references_are_stable_and_deduplicated():
    candidate = _candidate()
    assert candidate.evidence_refs == ("receipt:bridge-1", "receipt:integrity-1")
    second = _candidate()
    assert second.candidate_id == candidate.candidate_id


def test_failed_integrity_does_not_become_ready():
    candidate = _candidate("INTEGRITY_FAILED")
    assert candidate.lifecycle_status == "FAIL_CLOSED"


def test_unknown_status_fails_closed():
    candidate = _candidate("UNKNOWN")
    assert candidate.lifecycle_status == "FAIL_CLOSED"
