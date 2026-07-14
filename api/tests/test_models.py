"""Bounded API contract tests for the internal governed bridge.

These tests intentionally avoid provider calls, execution, publication, and
external authority. They verify only the request/response contract needed by
the repository's existing api-tests job.
"""

from app.models import RunRequest, RunResponse


def test_run_request_human_gate_is_exception_only_by_default():
    request = RunRequest(slug="contract-test", question="test")

    assert request.human_gate is False
    assert request.strategy == "consensus"
    assert request.trace_level == "full"


def test_run_response_accepts_governed_non_execution_states():
    common = {
        "session_path": "sessions/contract-test",
        "strategy": "consensus",
        "turns": [],
    }

    for status in ("OK", "PAUSED_FOR_REVIEW", "DENIED", "DEFERRED"):
        response = RunResponse(status=status, **common)
        assert response.status == status


def test_denied_response_does_not_require_final_output():
    response = RunResponse(
        status="DENIED",
        session_path="sessions/denied",
        strategy="consensus",
        turns=[],
        final=None,
        requires_human=False,
    )

    assert response.final is None
    assert response.requires_human is False
