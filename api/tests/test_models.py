"""Bounded API contract tests for the internal governed bridge.

These tests intentionally avoid provider calls, execution, publication, and
external authority. They verify only the request/response contract needed by
the repository's existing api-tests job.
"""

from app.models import (
    ArtifactManifest,
    EcosystemChatInferenceSession,
    ExternalInferenceComparisonInput,
    ExternalInferenceObservationRef,
    IntegrityEvidence,
    RunRequest,
    RunResponse,
)


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


def _external_session():
    return EcosystemChatInferenceSession(
        session_id="chat-session-1",
        node_id="node-1",
        receipt_1_sha256="sha256:" + "1" * 64,
        prompt_sha256="sha256:" + "2" * 64,
        observations=[
            ExternalInferenceObservationRef(
                observation_id="obs-openai",
                provider="openai",
                model="gpt-observed",
                request_correlation="request-a",
                response_sha256="sha256:" + "3" * 64,
                observation_state="RETAINED",
            ),
            ExternalInferenceObservationRef(
                observation_id="obs-anthropic",
                provider="anthropic",
                model=None,
                request_correlation="request-b",
                response_sha256="sha256:" + "4" * 64,
                observation_state="FAILED",
            ),
        ],
    )


def test_ecosystem_chat_external_inference_is_evidence_only():
    session = _external_session()
    assert session.authority_effect == "NONE"
    assert all(item.authority_effect == "NONE" for item in session.observations)
    assert session.retained_observation_ids() == {"obs-openai"}


def test_comparison_accepts_only_retained_observation_references():
    session = _external_session()
    comparison = ExternalInferenceComparisonInput(
        session_id=session.session_id,
        observation_refs=["obs-openai"],
    )
    session.require_retained_references(comparison.observation_refs)


def test_comparison_fails_closed_on_missing_or_failed_response_evidence():
    session = _external_session()
    for refs in ([], ["obs-anthropic"], ["obs-missing"], ["obs-openai", "obs-openai"]):
        try:
            session.require_retained_references(refs)
        except ValueError:
            pass
        else:
            raise AssertionError("comparison must fail closed on unusable evidence")


def test_provider_disagreement_is_not_collapsed_by_contract():
    session = EcosystemChatInferenceSession(
        session_id="chat-disagreement",
        node_id="node-1",
        receipt_1_sha256="sha256:" + "5" * 64,
        prompt_sha256="sha256:" + "6" * 64,
        observations=[
            ExternalInferenceObservationRef(
                observation_id="obs-a", provider="provider-a", model="model-a",
                request_correlation="a", response_sha256="sha256:" + "7" * 64,
                observation_state="RETAINED",
            ),
            ExternalInferenceObservationRef(
                observation_id="obs-b", provider="provider-b", model="model-b",
                request_correlation="b", response_sha256="sha256:" + "8" * 64,
                observation_state="RETAINED",
            ),
        ],
    )
    session.require_retained_references(["obs-a", "obs-b"])
    assert [o.response_sha256 for o in session.observations] == [
        "sha256:" + "7" * 64, "sha256:" + "8" * 64
    ]


def test_capability_descriptor_keeps_entitlement_separate_from_provider_availability():
    from app.models import CapabilityDescriptor
    cap = CapabilityDescriptor(
        capability_id="image-generate",
        work_class="image",
        input_media=["text"],
        output_media=["image"],
        provider="example-image-provider",
        entitlement_state="NOT_ENTITLED",
        routing_disposition="UPGRADE_REQUIRED",
        required_tier="pro",
        execution_constraints={"ephemeral_surface": True},
    )
    assert cap.routing_disposition == "UPGRADE_REQUIRED"
    assert cap.evidence_return == "RETAINED_OBSERVATION_REQUIRED"
    assert cap.authority_effect == "NONE"


def test_external_observation_can_retain_non_text_capability_identity():
    obs = ExternalInferenceObservationRef(
        observation_id="obs-image",
        provider="example-image-provider",
        model="image-model",
        capability_id="image-generate",
        work_class="image",
        input_media=["text"],
        output_media=["image"],
        request_correlation="req-image",
        response_sha256="sha256:" + "a" * 64,
        observation_state="RETAINED",
    )
    assert obs.work_class == "image"
    assert obs.output_media == ["image"]
    assert obs.authority_effect == "NONE"
