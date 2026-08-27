"""Tests for the fail-closed TV/TVC delegation transport boundary."""
import json

from scripts.transport_delegation_outbox import transport


def test_missing_token_requires_admitted_tvc_transport(tmp_path):
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    (outbox / "candidate.json").write_text("{}", encoding="utf-8")
    state = transport(outbox, tmp_path / "state.json", None)
    assert state["status"] == "TVC_ADMITTED_TRANSPORT_REQUIRED"
    assert state["pending_count"] == 1
    assert state["credential_authority"] == "TV/TVC"
    assert state["credential_material_present"] is False
    assert state["consumer_token_accepted"] is False
    assert state["transport_performed"] is False
    assert state["authority_effect"] == "NONE"
    assert state["manual_action_required"] is False


def test_legacy_token_argument_never_authorizes_transport(monkeypatch, tmp_path):
    def network_forbidden(*args, **kwargs):
        raise AssertionError("consumer-side transport network execution is prohibited")
    monkeypatch.setattr("urllib.request.urlopen", network_forbidden)
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    (outbox / "candidate.json").write_text(
        json.dumps({"candidate_id": "candidate"}),
        encoding="utf-8",
    )
    state = transport(outbox, tmp_path / "state.json", "legacy-token")
    assert state["status"] == "TVC_ADMITTED_TRANSPORT_REQUIRED"
    assert state["transmitted"] == []
    assert state["credential_material_present"] is False
    assert state["consumer_token_accepted"] is False
    assert state["transport_performed"] is False


def test_empty_outbox_still_preserves_authority_boundary(tmp_path):
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    state = transport(outbox, tmp_path / "state.json", None)
    assert state["pending_count"] == 0
    assert state["status"] == "TVC_ADMITTED_TRANSPORT_REQUIRED"
    assert state["transport_performed"] is False
    assert state["authority_effect"] == "NONE"
