import asyncio

from app.governance.discovery import ProviderDiscoveryEngine
from app.providers.local_runtime import LaunchPlan, LocalModel, RuntimeObservation


class FakeLocalManager:
    async def discover(self):
        return [
            RuntimeObservation(
                runtime_id="ollama",
                display_name="Ollama",
                endpoint="http://127.0.0.1:11434/api/tags",
                provider_type="ollama_text",
                status="ready",
                http_status=200,
                latency_ms=1.0,
                executable_present=True,
                models=[LocalModel(name="stegverse-local:v1", digest="sha256:model")],
            )
        ]

    def launch_plan(self, runtime_id):
        return LaunchPlan(
            runtime_id=runtime_id,
            executable_present=True,
            argv=["ollama", "serve"],
            safe_to_auto_launch=True,
            reason="bounded credential-free launch command available",
        )


def test_scan_local_uses_canonical_runtime_inventory():
    engine = ProviderDiscoveryEngine(local_manager=FakeLocalManager())
    results = asyncio.run(engine.scan_local())
    assert len(results) == 1
    result = results[0]
    assert result.provider_id == "ollama"
    assert result.status == "available"
    assert result.requires_api_key is False
    assert result.config_template["proof_required"] is True
    assert result.config_template["models"] == ["stegverse-local:v1"]
    assert "local_runtime_proof.py" in " ".join(result.instructions)


def test_scan_environment_is_tv_tvc_descriptive_not_secret_discovery(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    engine = ProviderDiscoveryEngine(local_manager=FakeLocalManager())
    results = asyncio.run(engine.scan_environment())
    openai = next(item for item in results if item.provider_id == "openai")
    assert openai.status == "discoverable"
    assert openai.connection_method == "tv_tvc"
    assert openai.config_template["credential_authority"] == "TV/TVC"
    rendered = " ".join(openai.instructions)
    assert "must-not-be-used" not in rendered
    assert "TV/TVC" in rendered


def test_query_known_provider_routes_credentials_to_tv_tvc():
    engine = ProviderDiscoveryEngine(local_manager=FakeLocalManager())
    result = engine.query_provider("openai")
    assert result.provider_id == "openai"
    assert result.provider_name == "OpenAI"
    assert result.status == "discoverable"
    assert result.connection_method == "tv_tvc"


def test_query_ollama_uses_installed_proof_path():
    engine = ProviderDiscoveryEngine(local_manager=FakeLocalManager())
    result = engine.query_provider("ollama")
    assert result.provider_id == "ollama"
    assert result.requires_api_key is False
    assert result.requires_network is False
    assert "local_runtime_proof.py" in " ".join(result.instructions)


def test_query_unknown_provider_fails_closed():
    engine = ProviderDiscoveryEngine(local_manager=FakeLocalManager())
    result = engine.query_provider("totally_unknown_provider_xyz")
    assert result.status == "denied"
    assert "not recognized" in result.reason.lower()


def test_query_custom_openai_compatible_keeps_tv_tvc_authority():
    engine = ProviderDiscoveryEngine(local_manager=FakeLocalManager())
    result = engine.query_provider("my_custom_api_endpoint")
    assert result.status == "discoverable"
    assert result.connection_method == "tv_tvc"
    assert "TV/TVC" in " ".join(result.instructions)
