"""Direct run-boundary tests without provider, network, or execution calls."""
from app.governance.artifact_integrity import evaluate_artifact_integrity
from app.governance.run_boundary import (
    build_integrity_ledger_payload,
    decide_run_boundary,
)


def test_allowed_complete_artifact_may_enter_accepted_result_ingestion():
    integrity = evaluate_artifact_integrity("# Purpose\nText\n# Status\nReady", ["Purpose", "Status"])
    decision = decide_run_boundary(
        provider_status="OK",
        provider_decision="allow",
        integrity=integrity,
    )
    assert decision.status == "OK"
    assert decision.may_ingest_accepted_result is True
    assert decision.requires_human is False


def test_allowed_incomplete_artifact_is_not_ingested_as_accepted_result():
    integrity = evaluate_artifact_integrity("# Purpose\nText", ["Purpose", "Status"])
    decision = decide_run_boundary(
        provider_status="OK",
        provider_decision="allow",
        integrity=integrity,
    )
    assert decision.status == "NEEDS_REPAIR"
    assert decision.may_ingest_accepted_result is False
    assert integrity.missing_sections == ("Status",)


def test_allowed_empty_artifact_fails_closed_before_accepted_ingestion():
    integrity = evaluate_artifact_integrity("", ["Purpose"])
    decision = decide_run_boundary(
        provider_status="OK",
        provider_decision="allow",
        integrity=integrity,
    )
    assert decision.status == "INTEGRITY_FAILED"
    assert decision.may_ingest_accepted_result is False


def test_denied_candidate_preserves_event_but_is_not_accepted_result():
    decision = decide_run_boundary(
        provider_status="DENIED",
        provider_decision="deny",
        integrity=None,
    )
    assert decision.status == "ADMISSIBILITY_FAILED"
    assert decision.preserve_governance_event is True
    assert decision.may_ingest_accepted_result is False


def test_deferred_candidate_routes_only_to_exception_review():
    decision = decide_run_boundary(
        provider_status="DEFERRED",
        provider_decision="defer",
        integrity=None,
    )
    assert decision.status == "EXCEPTION_REVIEW"
    assert decision.requires_human is True
    assert decision.may_ingest_accepted_result is False


def test_explicit_human_gate_cannot_convert_integrity_pass_into_commit_authority():
    integrity = evaluate_artifact_integrity("# Purpose\nText", ["Purpose"])
    decision = decide_run_boundary(
        provider_status="OK",
        provider_decision="allow",
        integrity=integrity,
        human_gate=True,
    )
    assert decision.status == "EXCEPTION_REVIEW"
    assert decision.requires_human is True
    assert decision.may_ingest_accepted_result is False


def test_integrity_ledger_payload_preserves_hash_manifest_and_pending_admissibility():
    integrity = evaluate_artifact_integrity("# Purpose\nText", ["Purpose", "Status"])
    boundary = decide_run_boundary(
        provider_status="OK",
        provider_decision="allow",
        integrity=integrity,
    )
    payload = build_integrity_ledger_payload(
        run_id="run-123",
        artifact_id="artifact-123",
        integrity=integrity,
        boundary=boundary,
    )
    assert payload["run_id"] == "run-123"
    assert payload["artifact_id"] == "artifact-123"
    assert len(payload["content_sha256"]) == 64
    assert payload["missing_sections"] == ["Status"]
    assert payload["integrity_decision"] == "NEEDS_REPAIR"
    assert payload["accepted_result_ingestion_permitted"] is False
    assert payload["downstream_admissibility"] == "PENDING"
