"""Every non-ALLOW provider result carries the six conformance fields."""
import asyncio

import httpx
import pytest

from app.governance.tv_tvc import TVCClient, TVProviderAdapter
from app.providers.custom_template import CustomProviderTemplate
from app.providers.disposition import OWNING_EXISTING_GOAL, SIX_FIELDS
from app.providers.mock_text import MockText
from app.providers.ollama_text import OllamaText
from app.registry import FACTORY
from app.tasks import Task


def _assert_six_fields(result):
    assert "text" not in result
    for key in SIX_FIELDS:
        assert isinstance(result.get(key), str) and result[key], key
    assert result["owning_existing_goal"] == OWNING_EXISTING_GOAL
    assert result["disposition"] in {"FAIL_CLOSED", "DENY"}
    assert result["authority_effect"] is False
    assert result["provider_execution_performed"] is False
    # legacy keys stay readable
    assert result["state"] and result["error"]


def _run(provider, task):
    return asyncio.run(provider.run(task))


@pytest.mark.parametrize("ptype", sorted(FACTORY))
def test_unsupported_task_is_six_field_deny(ptype):
    provider = FACTORY[ptype]("p")
    result = _run(provider, Task("image-generate", "x", {}))
    _assert_six_fields(result)
    assert result["disposition"] == "DENY"
    assert result["failure_code"] == "UNSUPPORTED_TASK_TYPE"


@pytest.mark.parametrize("ptype", sorted(FACTORY))
def test_every_registered_provider_non_allow_is_six_field(ptype, monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE", "http://127.0.0.1:9")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "2")
    provider = FACTORY[ptype]("p")
    result = _run(provider, Task("text-generate", "hello", {}))
    if "text" in result:
        assert ptype == "mock_text"
        return
    _assert_six_fields(result)


def test_blocked_external_provider_keeps_legacy_state():
    result = _run(FACTORY["openai_text"]("p"), Task("text-generate", "hello", {}))
    assert result["state"] == "BLOCKED"
    assert result["failure_code"] == "TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED"
    assert result["credential_material_present"] is False


def test_tv_provider_adapter_is_six_field():
    adapter = TVProviderAdapter(MockText("mock"), TVCClient(), "cred-mock")
    _assert_six_fields(_run(adapter, Task("text-generate", "hello", {})))


def test_ollama_unreachable_is_six_field_without_waiting(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE", "http://127.0.0.1:9")
    result = _run(OllamaText("local"), Task("text-generate", "hello", {}))
    _assert_six_fields(result)
    assert result["failure_code"] == "PROVIDER_ENDPOINT_UNAVAILABLE"


def test_custom_template_errors_are_six_field(monkeypatch):
    monkeypatch.setenv("YOUR_PROVIDER_API_KEY", "placeholder")
    monkeypatch.setenv("YOUR_PROVIDER_BASE", "http://127.0.0.1:9")
    provider = CustomProviderTemplate("custom")
    _assert_six_fields(_run(provider, Task("text-generate", "hello", {})))
    _assert_six_fields(_run(provider, Task("image-generate", "x", {})))
