"""Tests for TV/TVC ephemeral secret management."""
import pytest
import os
import time
import tempfile
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cge_light"))

from app.governance.tv_tvc import TVCClient, TVProviderAdapter, EphemeralCredential
from app.governance.entity import EntityIdentity


class TestEphemeralCredential:
    def test_creation(self):
        cred = EphemeralCredential(
            credential_id="cred-test",
            provider_type="openai_text",
            token="sk-test",
            expires_at=time.time() + 3600,
        )
        assert cred.credential_id == "cred-test"
        assert not cred.is_expired
        assert cred.ttl_seconds > 0

    def test_expiry(self):
        cred = EphemeralCredential(
            credential_id="cred-expired",
            provider_type="openai_text",
            token="sk-expired",
            expires_at=time.time() - 1,
        )
        assert cred.is_expired
        assert cred.ttl_seconds == 0

    def test_ttl_precision(self):
        cred = EphemeralCredential(
            credential_id="cred-ttl",
            provider_type="openai_text",
            token="sk-ttl",
            expires_at=time.time() + 300,
        )
        assert 295 <= cred.ttl_seconds <= 300


class TestTVCClient:
    def test_init_direct_mode(self):
        client = TVCClient(
            mode="direct",
            tvc_endpoint="https://tvc.test",
            tvc_api_key="test-key",
        )
        assert client.mode == "direct"
        assert client.endpoint == "https://tvc.test"

    def test_init_file_mode(self):
        client = TVCClient(mode="file")
        assert client.mode == "file"

    def test_init_env_mode(self):
        client = TVCClient(mode="env")
        assert client.mode == "env"

    def test_cache_invalidation(self):
        client = TVCClient(mode="env")
        cred = EphemeralCredential(
            credential_id="cred-cache",
            provider_type="openai_text",
            token="sk-cache",
            expires_at=time.time() + 3600,
        )
        client._cache["cred-cache"] = cred
        assert client._cache["cred-cache"] == cred

        client.invalidate("cred-cache")
        assert "cred-cache" not in client._cache

    def test_invalidate_all(self):
        client = TVCClient(mode="env")
        for i in range(3):
            client._cache[f"cred-{i}"] = EphemeralCredential(
                credential_id=f"cred-{i}",
                provider_type="openai_text",
                token=f"sk-{i}",
                expires_at=time.time() + 3600,
            )
        assert len(client._cache) == 3
        client.invalidate_all()
        assert len(client._cache) == 0

    def test_get_cache_status(self):
        client = TVCClient(mode="env")
        client._cache["cred-1"] = EphemeralCredential(
            credential_id="cred-1",
            provider_type="openai_text",
            token="sk-1",
            expires_at=time.time() + 3600,
        )
        status = client.get_cache_status()
        assert status["cached_count"] == 1
        assert status["entries"][0]["credential_id"] == "cred-1"

    @pytest.mark.asyncio
    async def test_fetch_env_success(self):
        os.environ["EPHEMERAL_OPENAI_KEY"] = "sk-ephemeral-test"
        os.environ["EPHEMERAL_OPENAI_KEY_EXPIRES"] = str(time.time() + 900)

        client = TVCClient(mode="env")
        cred = client._fetch_env("cred-openai", "openai_text")

        assert cred is not None
        assert cred.token == "sk-ephemeral-test"
        assert cred.provider_type == "openai_text"

        del os.environ["EPHEMERAL_OPENAI_KEY"]
        del os.environ["EPHEMERAL_OPENAI_KEY_EXPIRES"]

    @pytest.mark.asyncio
    async def test_fetch_env_missing(self):
        # Ensure env var is not set
        if "EPHEMERAL_OPENAI_KEY" in os.environ:
            del os.environ["EPHEMERAL_OPENAI_KEY"]

        client = TVCClient(mode="env")
        cred = client._fetch_env("cred-openai", "openai_text")
        assert cred is None

    @pytest.mark.asyncio
    async def test_fetch_file_success(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            vault = {
                "cred-test": {
                    "token": "sk-file-test",
                    "expires_at": time.time() + 3600,
                    "scope": ["text-generate"],
                }
            }
            json.dump(vault, f)
            vault_path = f.name

        os.environ["TV_VAULT_PATH"] = vault_path
        client = TVCClient(mode="file")
        cred = client._fetch_file("cred-test", "openai_text")

        assert cred is not None
        assert cred.token == "sk-file-test"

        os.unlink(vault_path)
        del os.environ["TV_VAULT_PATH"]

    @pytest.mark.asyncio
    async def test_fetch_file_missing(self):
        client = TVCClient(mode="file")
        cred = client._fetch_file("cred-nonexistent", "openai_text")
        assert cred is None


class TestTVProviderAdapter:
    def test_adapter_properties(self):
        from app.providers.mock_text import MockText

        mock = MockText("mock")
        tvc = TVCClient(mode="env")
        adapter = TVProviderAdapter(mock, tvc, "cred-mock")

        assert adapter.name == "mock"
        assert adapter.type == "mock_text"
        assert adapter.supports("text-generate")

    def test_token_injection_and_clear(self):
        from app.providers.openai_text import OpenAIText

        # Create a mock-like provider for testing
        class FakeProvider:
            def __init__(self):
                self.name = "fake"
                self.type = "fake_text"
                self.capabilities = ["text-generate"]
                self.headers = {"Authorization": "Bearer old"}

            def supports(self, t):
                return t in self.capabilities

            async def run(self, task):
                return {"text": "ok"}

        fake = FakeProvider()
        tvc = TVCClient(mode="env")
        adapter = TVProviderAdapter(fake, tvc, "cred-fake")

        # Inject token
        adapter._inject_token("sk-new")
        assert fake.headers["Authorization"] == "Bearer sk-new"

        # Clear token
        adapter._clear_token()
        assert adapter._last_token is None
