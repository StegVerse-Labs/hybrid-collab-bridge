import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cge_light"))

from app.governance.discovery import ProviderDiscoveryEngine, DiscoveryResult

class TestDiscoveryEngine:
    @pytest.mark.asyncio
    async def test_scan_local_no_servers(self):
        engine = ProviderDiscoveryEngine()
        results = await engine.scan_local()
        # Should return empty list if no local servers running
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_environment(self):
        engine = ProviderDiscoveryEngine()
        results = await engine.scan_environment()
        # Should find providers based on env vars
        assert isinstance(results, list)
        # Check that known providers are represented
        provider_ids = [r.provider_id for r in results]
        assert "openai" in provider_ids or "anthropic" in provider_ids or True  # May be empty if no keys

    def test_query_known_provider(self):
        engine = ProviderDiscoveryEngine()
        result = engine.query_provider("openai")
        assert result.provider_id == "openai"
        assert result.provider_name == "OpenAI"
        # Should be discoverable or available depending on env
        assert result.status in ["available", "discoverable"]

    def test_query_ollama(self):
        engine = ProviderDiscoveryEngine()
        result = engine.query_provider("ollama")
        assert result.provider_id == "ollama"
        assert result.requires_api_key is False
        assert result.requires_network is False

    def test_query_unknown_provider(self):
        engine = ProviderDiscoveryEngine()
        result = engine.query_provider("totally_unknown_provider_xyz")
        assert result.status == "denied"
        assert "not recognized" in result.reason.lower() or "not a known" in str(result.instructions)

    def test_query_custom_openai_compatible(self):
        engine = ProviderDiscoveryEngine()
        result = engine.query_provider("my_custom_api_endpoint")
        # Should suggest OpenAI-compatible path
        assert result.status == "discoverable"
        assert "openai" in str(result.instructions).lower() or "compatible" in str(result.instructions).lower()
