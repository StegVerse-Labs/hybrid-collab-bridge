"""Regression tests for the current TV/TVC consumer credential boundary."""
from pathlib import Path

import pytest

from app.governance.tv_tvc import (
    BLOCKED_REASON,
    EphemeralCredential,
    TVCClient,
    TVProviderAdapter,
)
from app.providers.anthropic_text import AnthropicText
from app.providers.deepseek_text import DeepSeekText
from app.providers.gemini_text import GeminiText
from app.providers.grok_text import GrokText
from app.providers.kimi_text import KimiText
from app.providers.openai_text import OpenAIText
from app.providers.perplexity_text import PerplexityText
from app.providers.mock_text import MockText
from app.tasks import Task


ROOT = Path(__file__).resolve().parents[2]


def test_compatibility_credential_carries_no_secret_material():
    record = EphemeralCredential(
        credential_id="cred-test",
        provider_type="openai_text",
    )
    assert not hasattr(record, "token")
    assert record.credential_material_present is False
    assert record.is_expired is True
    assert record.ttl_seconds == 0.0


@pytest.mark.asyncio
async def test_tvc_client_never_returns_or_retains_credential_material():
    client = TVCClient(
        mode="env",
        tvc_endpoint="https://example.invalid",
        tvc_api_key="must-not-be-retained",
    )
    assert client.mode == "admitted-route-only"
    assert client.api_key is None
    assert await client.get_credential("cred-openai", "openai_text") is None
    assert await client.get_credential_with_fallback(
        "cred-openai",
        "openai_text",
        env_fallback="OPENAI_KEY",
    ) is None

    status = client.get_cache_status()
    assert status["state"] == "BLOCKED"
    assert status["reason"] == BLOCKED_REASON
    assert status["cached_count"] == 0
    assert status["credential_material_present"] is False
    assert status["authority_effect"] is False


@pytest.mark.asyncio
async def test_legacy_provider_adapter_fails_closed_without_secret_injection():
    base = MockText("mock")
    adapter = TVProviderAdapter(base, TVCClient(), "cred-mock")
    task = Task("text-generate", "hello", {})

    result = await adapter.run(task)
    assert result["state"] == "BLOCKED"
    assert result["error"] == BLOCKED_REASON
    assert result["credential_material_present"] is False
    assert result["provider_execution_performed"] is False
    assert result["authority_effect"] is False
    assert not hasattr(adapter, "_inject_token")
    assert not hasattr(adapter, "_last_token")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_cls",
    [
        OpenAIText,
        AnthropicText,
        GeminiText,
        DeepSeekText,
        GrokText,
        KimiText,
        PerplexityText,
    ],
)
async def test_external_provider_adapters_are_non_credential_bearing_and_fail_closed(
    provider_cls,
):
    provider = provider_cls("external")
    result = await provider.run(Task("text-generate", "hello", {}))

    assert result["state"] == "BLOCKED"
    assert result["error"] == BLOCKED_REASON
    assert result["credential_material_present"] is False
    assert result["provider_execution_performed"] is False
    assert result["authority_effect"] is False


def test_retired_consumer_secret_sources_cannot_return():
    governed = (ROOT / "api/app/governance/tv_tvc.py").read_text(encoding="utf-8")
    registry = (ROOT / "api/app/registry.py").read_text(encoding="utf-8")

    for forbidden in (
        "/v1/vault/unseal",
        "TV_VAULT_PATH",
        "EPHEMERAL_OPENAI",
        "EPHEMERAL_ANTHROPIC",
        "EPHEMERAL_MOONSHOT",
        "TVC_MODE",
        "_fetch_env",
        "_fetch_file",
        "_inject_token",
    ):
        assert forbidden not in governed

    for forbidden in (
        "TVC_MODE",
        "TVCClient",
        "TVProviderAdapter",
        "TVC fallback activated",
    ):
        assert forbidden not in registry


def test_external_provider_sources_contain_no_direct_secret_or_network_use():
    paths = (
        "api/app/providers/openai_text.py",
        "api/app/providers/anthropic_text.py",
        "api/app/providers/gemini_text.py",
        "api/app/providers/deepseek_text.py",
        "api/app/providers/grok_text.py",
        "api/app/providers/kimi_text.py",
        "api/app/providers/perplexity_text.py",
    )
    forbidden = (
        "API_KEY",
        "x-api-key",
        'headers={"Authorization"',
        "httpx.AsyncClient",
        "genai.configure",
    )

    for relative in paths:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, f"{relative} reintroduced {marker}"
        assert "TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED" in text or "openai_text import OpenAIText" in text
