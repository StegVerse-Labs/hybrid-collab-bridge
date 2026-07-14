"""Tests for token-gated delegation transport."""
import json

from scripts.transport_delegation_outbox import transport


def test_missing_token_records_external_authority_block_without_manual_task(tmp_path):
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    (outbox / "candidate.json").write_text("{}", encoding="utf-8")
    state = transport(outbox, tmp_path / "state.json", None)
    assert state["status"] == "BLOCKED_EXTERNAL_AUTHORITY"
    assert state["pending_count"] == 1
    assert state["transport_authority_present"] is False
    assert state["manual_action_required"] is False


def test_empty_outbox_with_token_is_complete_without_network(monkeypatch, tmp_path):
    def fail_request(*args, **kwargs):
        raise AssertionError("network should not be called for empty outbox")

    monkeypatch.setattr("scripts.transport_delegation_outbox._request", fail_request)
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    state = transport(outbox, tmp_path / "state.json", "token")
    assert state["status"] == "TRANSPORT_COMPLETE"
    assert state["pending_count"] == 0
    assert state["transmitted"] == []
    assert state["manual_action_required"] is False


def test_authorized_transport_writes_destination_and_commit_evidence(monkeypatch, tmp_path):
    calls = []

    def fake_existing(repo, path, token):
        return None

    def fake_request(url, token, method="GET", body=None):
        calls.append((url, method, body))
        return {"commit": {"sha": "commit-123"}}

    monkeypatch.setattr("scripts.transport_delegation_outbox._existing_sha", fake_existing)
    monkeypatch.setattr("scripts.transport_delegation_outbox._request", fake_request)
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    (outbox / "candidate.json").write_text(json.dumps({"candidate_id": "candidate"}), encoding="utf-8")
    state = transport(outbox, tmp_path / "state.json", "token")
    assert state["status"] == "TRANSPORT_COMPLETE"
    assert state["transmitted"][0]["commit_sha"] == "commit-123"
    assert "StegVerse-Labs/Ecosystem-Delegation" in state["transmitted"][0]["destination"]
    assert calls[0][1] == "PUT"
