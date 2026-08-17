import asyncio

from app.governance.discovery import ProviderDiscoveryEngine


def test_scan_local_reports_machine_owned_canonical_route_without_launch_authority():
    engine = ProviderDiscoveryEngine()
    results = asyncio.run(engine.scan_local())
    assert len(results) == 1
    result = results[0]
    assert result.provider_id == "stegverse_sovereign_local_model"
    assert result.status == "machine_owned"
    assert result.connection_method == "tvc_route"
    assert result.requires_api_key is False
    assert result.config_template["credential_requirement"] == "NONE"
    assert result.config_template["route_authority"] == "StegVerse-Labs/TVC"
    assert result.config_template["canonical_model_owner"] == "StegVerse-002/micro-node-runtime#22"
    rendered = " ".join(result.instructions)
    assert "micro-node-runtime#22" in rendered
    assert "must not launch" in rendered


def test_scan_environment_is_tv_tvc_descriptive_not_secret_discovery(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    engine = ProviderDiscoveryEngine()
    results = asyncio.run(engine.scan_environment())
    openai = next(item for item in results if item.provider_id == "openai")
    assert openai.status == "discoverable"
    assert openai.connection_method == "tv_tvc"
    assert openai.config_template["credential_authority"] == "TV/TVC"
    rendered = " ".join(openai.instructions)
    assert "must-not-be-used" not in rendered
    assert "TV/TVC" in rendered


def test_query_known_provider_routes_credentials_to_tv_tvc():
    engine = ProviderDiscoveryEngine()
    result = engine.query_provider("openai")
    assert result.provider_id == "openai"
    assert result.provider_name == "OpenAI"
    assert result.status == "discoverable"
    assert result.connection_method == "tv_tvc"


def test_query_ollama_redirects_to_canonical_sovereign_route():
    engine = ProviderDiscoveryEngine()
    result = engine.query_provider("ollama")
    assert result.provider_id == "stegverse_sovereign_local_model"
    assert result.status == "machine_owned"
    assert result.requires_api_key is False
    assert result.requires_network is False
    assert result.connection_method == "tvc_route"
    assert result.config_template["machine_owned_activation"] is True


def test_query_unknown_provider_fails_closed():
    engine = ProviderDiscoveryEngine()
    result = engine.query_provider("totally_unknown_provider_xyz")
    assert result.status == "denied"
    assert "not recognized" in result.reason.lower()


def test_query_custom_openai_compatible_keeps_tv_tvc_authority():
    engine = ProviderDiscoveryEngine()
    result = engine.query_provider("my_custom_api_endpoint")
    assert result.status == "discoverable"
    assert result.connection_method == "tv_tvc"
    assert result.config_template["route_authority"] == "StegVerse-Labs/TVC"
    assert "TV/TVC" in " ".join(result.instructions)
