import asyncio

import pytest

from app.providers.local_runtime import LocalRuntimeManager, LocalRuntimeProof


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, url):
        return self.responses[url]


def test_ollama_discovery_and_proof_are_credential_free():
    responses = {
        "http://127.0.0.1:11434/api/tags": FakeResponse(
            200,
            {
                "models": [
                    {
                        "name": "stegverse-local:latest",
                        "digest": "sha256:modeldigest",
                        "size": 123,
                    }
                ]
            },
        ),
        "http://127.0.0.1:8080/v1/models": FakeResponse(200, {"data": []}),
        "http://127.0.0.1:8000/v1/models": FakeResponse(200, {"data": []}),
    }
    manager = LocalRuntimeManager(
        command_finder=lambda _: "/usr/bin/runtime",
        client_factory=lambda: FakeClient(responses),
    )

    observations = asyncio.run(manager.discover())
    ollama = next(item for item in observations if item.runtime_id == "ollama")
    assert ollama.status == "ready"
    assert ollama.models[0].name == "stegverse-local:latest"

    proof = asyncio.run(manager.prove("ollama", "stegverse-local:latest"))
    assert proof.runtime_ready is True
    assert proof.credential_material_present is False
    assert proof.model_profile.credential_required is False
    assert proof.model_profile.model_digest == "sha256:modeldigest"
    assert LocalRuntimeManager.validate_proof(proof) is True


def test_launch_policy_allows_only_bounded_ollama_server_start():
    manager = LocalRuntimeManager(command_finder=lambda _: "/usr/bin/runtime")
    ollama = manager.launch_plan("ollama")
    llama = manager.launch_plan("llamacpp")
    vllm = manager.launch_plan("vllm")

    assert ollama.safe_to_auto_launch is True
    assert ollama.argv == ["ollama", "serve"]
    assert llama.safe_to_auto_launch is False
    assert vllm.safe_to_auto_launch is False


def test_missing_executable_fails_closed():
    manager = LocalRuntimeManager(command_finder=lambda _: None)
    plan = manager.launch_plan("ollama")
    assert plan.safe_to_auto_launch is False
    assert "not found" in plan.reason


def test_proof_requires_model_inventory():
    responses = {
        "http://127.0.0.1:11434/api/tags": FakeResponse(200, {"models": []}),
        "http://127.0.0.1:8080/v1/models": FakeResponse(200, {"data": []}),
        "http://127.0.0.1:8000/v1/models": FakeResponse(200, {"data": []}),
    }
    manager = LocalRuntimeManager(
        command_finder=lambda _: "/usr/bin/runtime",
        client_factory=lambda: FakeClient(responses),
    )
    with pytest.raises(RuntimeError):
        asyncio.run(manager.prove("ollama"))


def test_tampered_proof_is_rejected():
    from app.providers.local_runtime import LocalModelProfile

    profile = LocalModelProfile(
        schema="stegverse.local-model-profile.v1",
        runtime_id="ollama",
        endpoint="http://127.0.0.1:11434/api/tags",
        model_name="model",
        model_digest=None,
        capabilities=["text-generate", "local-inference"],
        credential_required=False,
        identity_hash="sha256:not-real",
    )
    proof = LocalRuntimeProof(
        schema="stegverse.local-runtime-proof.v1",
        observed_at="2026-08-17T00:00:00+00:00",
        runtime_id="ollama",
        endpoint="http://127.0.0.1:11434/api/tags",
        http_status=200,
        latency_ms=1.0,
        model_profile=profile,
        credential_material_present=False,
        runtime_ready=True,
        proof_hash="sha256:not-real",
    )
    assert LocalRuntimeManager.validate_proof(proof) is False
