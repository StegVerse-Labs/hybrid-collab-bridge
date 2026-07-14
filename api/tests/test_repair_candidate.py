"""Repair-candidate continuity and non-authority tests."""
import pytest

from app.governance.artifact_integrity import evaluate_artifact_integrity
from app.governance.repair_candidate import create_repair_candidate


def test_missing_section_repair_preserves_original_hash_and_run_identity():
    integrity = evaluate_artifact_integrity("# Purpose\nText", ["Purpose", "Status"])
    repair = create_repair_candidate(
        run_id="run-123",
        artifact_id="artifact-123",
        integrity=integrity,
    )
    assert repair.original_run_id == "run-123"
    assert repair.original_artifact_id == "artifact-123"
    assert repair.original_content_sha256 == integrity.content_sha256
    assert repair.missing_sections == ("Status",)
    assert repair.status == "DECLARED"
    assert repair.admissibility_result == "PENDING"
    assert repair.commit_time_validity == "PENDING"
    assert repair.action_ref is None
    assert repair.final_receipt_id is None


def test_repair_candidate_id_is_deterministic_for_same_evidence():
    integrity = evaluate_artifact_integrity("", ["Purpose"])
    first = create_repair_candidate(run_id="run-1", artifact_id=None, integrity=integrity)
    second = create_repair_candidate(run_id="run-1", artifact_id=None, integrity=integrity)
    assert first.repair_candidate_id == second.repair_candidate_id


def test_integrity_pass_cannot_create_repair_candidate():
    integrity = evaluate_artifact_integrity("# Purpose\nText", ["Purpose"])
    with pytest.raises(ValueError, match="NEEDS_REPAIR or FAIL_CLOSED"):
        create_repair_candidate(run_id="run-1", artifact_id="artifact-1", integrity=integrity)


def test_repair_candidate_requires_run_identity():
    integrity = evaluate_artifact_integrity("", ["Purpose"])
    with pytest.raises(ValueError, match="run_id is required"):
        create_repair_candidate(run_id="", artifact_id="artifact-1", integrity=integrity)
