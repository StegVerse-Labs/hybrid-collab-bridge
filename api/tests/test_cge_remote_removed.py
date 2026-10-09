"""The remote CGE mode is removed: embedded is the only mode (issue #38)."""
import asyncio
from pathlib import Path

import pytest

from app.governance import cge_client as cge_module
from app.governance.cge_client import CGELightClient, RemoteCGERemoved
from app.governance.entity import EntityIdentity

SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)

APP = Path(__file__).resolve().parents[1] / "app"


def _actor() -> EntityIdentity:
    return EntityIdentity(
        entity_id="test-actor",
        entity_type="automated_process",
        org_id="Test-Org",
        owner_human="owner",
        owner_ai="Beta_Orionis",
        capability_set=["test"],
    )


def _assert_six_field_fail_closed(result: dict, mode: str) -> None:
    for field in SIX_FIELDS:
        assert result.get(field), field
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failure_code"] == "REMOTE_CGE_REMOVED"
    assert result["owning_existing_goal"] == "HCB-VERSIONED-CONTRACT-038"
    assert result["requested_cge_mode"] == mode
    assert result["admissible"] is False
    assert result["remote_contacted"] is False


@pytest.mark.parametrize("mode", ["remote", "hybrid"])
def test_non_embedded_ingest_fails_closed_without_contact(tmp_path, no_remote_cge, mode):
    client = CGELightClient(org_id="Test-Org", mode=mode, cge_path=str(tmp_path / "cge"))
    result = asyncio.run(client.ingest({"x": 1}, source="test", actor=_actor()))
    _assert_six_field_fail_closed(result, mode)
    assert no_remote_cge == []


def test_non_embedded_ledger_append_raises_six_field_disposition(tmp_path, no_remote_cge):
    client = CGELightClient(org_id="Test-Org", mode="remote", cge_path=str(tmp_path / "cge"))
    with pytest.raises(RemoteCGERemoved) as exc:
        asyncio.run(client.append_ledger("approve", _actor(), {"x": 1}, {}, {}))
    _assert_six_field_fail_closed(exc.value.disposition, "remote")
    assert no_remote_cge == []


def test_client_has_no_endpoint_or_http_dependency():
    assert not hasattr(cge_module, "httpx")
    with pytest.raises(TypeError):
        CGELightClient(org_id="Test-Org", endpoint="http://remote-cge.invalid")
    assert not hasattr(CGELightClient, "_ingest_remote")


def test_no_application_code_reads_cge_endpoint():
    offenders = [
        str(path)
        for path in APP.rglob("*.py")
        if path.name != "cge_client.py" and "HCB_CGE_ENDPOINT" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
