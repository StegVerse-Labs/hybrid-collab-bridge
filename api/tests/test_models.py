"""Bounded API contract tests for the internal governed bridge.

These tests intentionally avoid provider calls, execution, publication, and
external authority. They verify only the request/response contract needed by
the repository's existing api-tests job.
"""

from app.models import ArtifactManifest, IntegrityEvidence, RunRequest, RunResponse


def test_run_request_human_gate_is_exception_only_by_default():
    request = RunRequest(slug="contract-test", question="test")

    assert request.human_gate is False
    assert request.strategy == "consensus"
    assert request.trace_level == "full"
    assert request.artifact_manifest is None


def test_run_request_accepts_declared_artifact_manifest():
    request = RunRequest(
        slug="manifest-test",
        question="generate artifact",
        artifact_manifest=ArtifactManifest(
            artifact_id="readme-root",
            required_sections=["Purpose", "Safety Rules", "Status"],
        ),
    )

    assert request.artifact_manifest is not None
    assert request.artifact_manifest.artifact_type == "text"
    assert request.artifact_manifest.required_sections == [
        "Purpose",
        "Safety Rules",
        "Status",
    ]


def test_run_response_accepts_explicit_governed_states():
    common = {
        "session_path": "sessions/contract-test",
        "strategy": "consensus",
        "turns": [],
    }

    statuses = (
        "OK",
        "NEEDS_REPAIR",
        "INTEGRITY_FAILED",
        "ADMISSIBILITY_FAILED",
        "EXCEPTION_REVIEW",
        # Retained for backward-compatible receipt reconstruction.
        "PAUSED_FOR_REVIEW",
        "DENIED",
        "DEFERRED",
    )
    for status in statuses:
        response = RunResponse(status=status, **common)
        assert response.status == status


def test_integrity_evidence_is_exposed_without_granting_authority():
    evidence = IntegrityEvidence(
        decision="NEEDS_REPAIR",
        content_sha256="0" * 64,
        required_sections=["Purpose", "Status"],
        missing_sections=["Status"],
        empty=False,
        reasoning="Artifact is missing one or more declared required sections.",
        passed=False,
    )
    response = RunResponse(
        status="NEEDS_REPAIR",
        session_path="sessions/needs-repair",
        strategy="consensus",
        integrity=evidence,
        requires_human=False,
    )

    assert response.integrity is not None
    assert response.integrity.decision == "NEEDS_REPAIR"
    assert response.integrity.passed is False
    assert response.requires_human is False


def test_admissibility_failure_does_not_require_final_output():
    response = RunResponse(
        status="ADMISSIBILITY_FAILED",
        session_path="sessions/denied",
        strategy="consensus",
        turns=[],
        final=None,
        requires_human=False,
    )

    assert response.final is None
    assert response.requires_human is False
