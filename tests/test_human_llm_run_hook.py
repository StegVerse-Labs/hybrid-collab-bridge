"""Tests for automatic /v1/run Human–LLM assessment attachment."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.app.governance import human_llm_run_hook as hook


def test_baseline_is_fail_closed_without_semantic_evidence():
    record = hook.assessment_for_run(
        {"slug": "run-1", "human_gate": False},
        {"session_path": "sessions/2026-07-24/run-1", "chain_id": "chain-1"},
    )
    assert record["trace_id"] == "chain-1"
    assert record["overall_outcome"] == "INDETERMINATE"
    assert record["tests"]["meaning_preservation"]["critical"] is True
    assert record["tests"]["meaning_preservation"]["status"] == "INDETERMINATE"
    assert record["review"]["comprehension_demonstrated"] is False


def test_supplied_assessment_is_preserved_as_independent_copy():
    supplied = {"assessment_id": "a-1", "tests": {}}
    selected = hook.assessment_for_run(
        {"interoperability_assessment": supplied},
        {"session_path": "sessions/run"},
    )
    assert selected == supplied
    assert selected is not supplied


def test_post_run_response_contains_governed_assessment(monkeypatch, tmp_path: Path):
    app = FastAPI(title="hook-test")
    session_dir = tmp_path / "sessions" / "run-1"
    session_dir.mkdir(parents=True)

    @app.post("/v1/run")
    async def run():
        return {"status": "OK", "session_path": str(session_dir), "chain_id": "chain-1"}

    captured = {}

    async def fake_submit(body, x_admin_token=None):
        captured["body"] = body
        captured["token"] = x_admin_token
        return SimpleNamespace(model_dump=lambda: {
            "assessment_id": body.assessment["assessment_id"],
            "trace_id": body.assessment["trace_id"],
            "outcome": body.assessment["overall_outcome"],
            "admission_decision": "deny",
            "publication_allowed": False,
            "errors": [],
            "receipt": {"verified": True},
            "session_artifact": str(session_dir / "04_human_llm_pair_assessment.json"),
        })

    monkeypatch.setattr(hook, "submit_assessment", fake_submit)
    assert hook.install_run_assessment_hook(app) is True
    assert hook.install_run_assessment_hook(app) is False

    client = TestClient(app)
    response = client.post(
        "/v1/run",
        headers={"X-ADMIN-TOKEN": "token-1"},
        json={"slug": "run-1", "question": "test"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["interoperability"]["outcome"] == "INDETERMINATE"
    assert payload["interoperability"]["publication_allowed"] is False
    assert captured["token"] == "token-1"
    assert captured["body"].reviewer_action == "automatic_post_run_attachment"
