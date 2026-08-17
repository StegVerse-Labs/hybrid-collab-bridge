"""StegVerse provider discovery with canonical local-runtime and TV/TVC boundaries.

Local inference discovery is credential-free and delegated to
``app.providers.local_runtime``. Cloud credential discovery never reads provider
API keys from this process: TV/TVC is the credential authority and must provide
a governed route/attestation outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..providers.local_runtime import LocalRuntimeManager


@dataclass
class DiscoveryResult:
    """Result of a provider discovery attempt."""

    provider_id: str
    provider_name: str
    provider_type: str
    status: str
    reason: str
    connection_method: str
    instructions: List[str] = field(default_factory=list)
    config_template: Dict[str, Any] = field(default_factory=dict)
    requires_network: bool = True
    requires_api_key: bool = True
    estimated_cost_tier: str = "unknown"


class ProviderDiscoveryEngine:
    """Discover providers without becoming a credential or execution authority."""

    CLOUD_PROVIDERS: Dict[str, Dict[str, Any]] = {
        "openai": {"name": "OpenAI", "type": "openai_text", "cost_tier": "premium"},
        "anthropic": {"name": "Anthropic (Claude)", "type": "anthropic_text", "cost_tier": "premium"},
        "moonshot": {"name": "Moonshot AI (Kimi)", "type": "kimi_text", "cost_tier": "standard"},
        "google": {"name": "Google (Gemini)", "type": "gemini_text", "cost_tier": "cheap"},
        "xai": {"name": "xAI (Grok)", "type": "grok_text", "cost_tier": "standard"},
        "deepseek": {"name": "DeepSeek", "type": "deepseek_text", "cost_tier": "cheap"},
        "perplexity": {"name": "Perplexity", "type": "perplexity_text", "cost_tier": "standard"},
    }

    def __init__(self, local_manager: LocalRuntimeManager | None = None) -> None:
        self.discovered: List[DiscoveryResult] = []
        self.local_manager = local_manager or LocalRuntimeManager()

    async def scan_all(self) -> List[DiscoveryResult]:
        results: List[DiscoveryResult] = []
        results.extend(await self.scan_local())
        results.extend(await self.scan_environment())
        results.extend(await self.scan_network())
        self.discovered = results
        return results

    async def scan_local(self) -> List[DiscoveryResult]:
        """Use the canonical loopback runtime inventory and launch policy."""
        results: List[DiscoveryResult] = []
        for observation in await self.local_manager.discover():
            plan = self.local_manager.launch_plan(observation.runtime_id)
            model_names = [model.name for model in observation.models]
            if observation.status == "ready":
                status = "available"
                reason = f"Verified local runtime with {len(model_names)} model(s) at {observation.endpoint}"
            elif observation.executable_present:
                status = "discoverable"
                reason = observation.error or "Runtime executable is installed but not ready"
            else:
                continue

            instructions = [
                "Local runtime path is credential-free; no provider token is required.",
                f"Runtime endpoint: {observation.endpoint}",
                f"Launch policy: {plan.reason}",
                f"Proof command: python scripts/local_runtime_proof.py --runtime {observation.runtime_id}",
            ]
            if plan.safe_to_auto_launch:
                instructions.append(
                    f"Bounded launch + proof: python scripts/local_runtime_proof.py --runtime {observation.runtime_id} --launch"
                )
            if model_names:
                instructions.append("Models: " + ", ".join(model_names[:10]))

            results.append(
                DiscoveryResult(
                    provider_id=observation.runtime_id,
                    provider_name=observation.display_name,
                    provider_type=observation.provider_type,
                    status=status,
                    reason=reason,
                    connection_method="local",
                    instructions=instructions,
                    config_template={
                        "name": observation.runtime_id,
                        "type": observation.provider_type,
                        "enabled": observation.status == "ready",
                        "endpoint": observation.endpoint,
                        "models": model_names,
                        "proof_required": True,
                        "credential_authority": "none-local",
                    },
                    requires_network=False,
                    requires_api_key=False,
                    estimated_cost_tier="free",
                )
            )
        return results

    async def scan_environment(self) -> List[DiscoveryResult]:
        """Describe cloud capability without inspecting provider secrets.

        The method name remains for API compatibility. It intentionally performs
        no environment-secret discovery; TV/TVC is the sole credential authority.
        """
        return [self._cloud_result(provider_id, info) for provider_id, info in self.CLOUD_PROVIDERS.items()]

    async def scan_network(self) -> List[DiscoveryResult]:
        """Do not probe arbitrary LAN hosts without a governed peer registry."""
        return []

    def query_provider(self, query: str) -> DiscoveryResult:
        query_lower = query.lower().strip()
        for provider_id, info in self.CLOUD_PROVIDERS.items():
            if query_lower in (provider_id, info["name"].lower(), info["type"].lower()):
                return self._cloud_result(provider_id, info)

        if query_lower in {"ollama", "local", "on-premise", "self-hosted"}:
            plan = self.local_manager.launch_plan("ollama")
            instructions = [
                "Canonical local runtime: Ollama loopback at http://127.0.0.1:11434.",
                "No provider API key or token is used by this path.",
                "Discover/prove: python scripts/local_runtime_proof.py --runtime ollama",
                "Formal StegVerse model development requires an already-installed local base model; downloads are not performed by the bridge.",
            ]
            if plan.safe_to_auto_launch:
                instructions.append("Launch + prove: python scripts/local_runtime_proof.py --runtime ollama --launch")
            else:
                instructions.append(f"Launch blocked until host condition changes: {plan.reason}")
            return DiscoveryResult(
                provider_id="ollama",
                provider_name="Ollama",
                provider_type="ollama_text",
                status="discoverable",
                reason="Canonical credential-free local runtime path is installed",
                connection_method="local",
                instructions=instructions,
                config_template={
                    "name": "ollama",
                    "type": "ollama_text",
                    "enabled": False,
                    "proof_required": True,
                    "credential_authority": "none-local",
                },
                requires_network=False,
                requires_api_key=False,
                estimated_cost_tier="free",
            )

        if any(keyword in query_lower for keyword in ("api", "openai", "compatible", "endpoint")):
            return DiscoveryResult(
                provider_id="custom_openai",
                provider_name=f"Custom: {query}",
                provider_type="openai_text",
                status="discoverable",
                reason="Potential OpenAI-compatible route requires governed configuration",
                connection_method="tv_tvc",
                instructions=[
                    "Register endpoint metadata through the governed StegVerse configuration path.",
                    "Any credential must be resolved by TV/TVC; do not place provider secrets in this bridge.",
                    "Connection availability is not execution authority.",
                ],
                config_template={
                    "name": "custom",
                    "type": "openai_text",
                    "enabled": False,
                    "credential_authority": "TV/TVC",
                },
                requires_network=True,
                requires_api_key=True,
                estimated_cost_tier="unknown",
            )

        return DiscoveryResult(
            provider_id="unknown",
            provider_name=query,
            provider_type="unknown",
            status="denied",
            reason=f"Provider '{query}' is not recognized by the governed discovery registry",
            connection_method="none",
            instructions=[
                "Do not infer or install an unrecognized provider automatically.",
                "Add a governed provider contract before use.",
            ],
            config_template={},
            requires_network=True,
            requires_api_key=True,
            estimated_cost_tier="unknown",
        )

    def _cloud_result(self, provider_id: str, info: Dict[str, Any]) -> DiscoveryResult:
        return DiscoveryResult(
            provider_id=provider_id,
            provider_name=info["name"],
            provider_type=info["type"],
            status="discoverable",
            reason="Provider capability is known; credential availability is intentionally not inspected here",
            connection_method="tv_tvc",
            instructions=[
                "Credential authority: TV/TVC.",
                "This bridge does not read, request, store, or advertise provider API-key environment variables.",
                "Resolve a governed TV/TVC route before attempting provider execution.",
            ],
            config_template={
                "name": provider_id,
                "type": info["type"],
                "enabled": False,
                "credential_authority": "TV/TVC",
            },
            requires_network=True,
            requires_api_key=True,
            estimated_cost_tier=info["cost_tier"],
        )
