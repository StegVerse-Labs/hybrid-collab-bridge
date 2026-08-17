"""StegVerse provider discovery with canonical TV/TVC authority boundaries.

This bridge is a discovery/consumer surface. It does not discover provider
secrets, launch sovereign model processes, create model proofs, or admit local
routes. Those authorities are already canonical elsewhere:

- model/runtime: StegVerse-002/micro-node-runtime#22
- live carrier: StegVerse-Labs/.github#60 / SHWP-DURABLE-RUNTIME-ACTIVATION
- route authority: StegVerse-Labs/TVC / TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002
- transport: StegVerse-org/LLM-adapter#18
- custody/reconstruction: master-records/orchestration
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DiscoveryResult:
    """Result of a provider discovery query without granting route authority."""

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
    """Describe available provider classes without becoming credential/runtime authority."""

    CLOUD_PROVIDERS: Dict[str, Dict[str, Any]] = {
        "openai": {"name": "OpenAI", "type": "openai_text", "cost_tier": "premium"},
        "anthropic": {"name": "Anthropic (Claude)", "type": "anthropic_text", "cost_tier": "premium"},
        "moonshot": {"name": "Moonshot AI (Kimi)", "type": "kimi_text", "cost_tier": "standard"},
        "google": {"name": "Google (Gemini)", "type": "gemini_text", "cost_tier": "cheap"},
        "xai": {"name": "xAI (Grok)", "type": "grok_text", "cost_tier": "standard"},
        "deepseek": {"name": "DeepSeek", "type": "deepseek_text", "cost_tier": "cheap"},
        "perplexity": {"name": "Perplexity", "type": "perplexity_text", "cost_tier": "standard"},
    }

    def __init__(self) -> None:
        self.discovered: List[DiscoveryResult] = []

    async def scan_all(self) -> List[DiscoveryResult]:
        results: List[DiscoveryResult] = []
        results.extend(await self.scan_local())
        results.extend(await self.scan_environment())
        results.extend(await self.scan_network())
        self.discovered = results
        return results

    async def scan_local(self) -> List[DiscoveryResult]:
        """Expose the canonical sovereign local-model route as machine-owned.

        Physical discovery/launch/proof is intentionally not repeated in this
        bridge. The canonical micro-node runtime and heartbeat own that work.
        """
        return [self._sovereign_local_result()]

    async def scan_environment(self) -> List[DiscoveryResult]:
        """Describe cloud capability without inspecting environment secrets."""
        return [self._cloud_result(provider_id, info) for provider_id, info in self.CLOUD_PROVIDERS.items()]

    async def scan_network(self) -> List[DiscoveryResult]:
        """Do not probe arbitrary LAN hosts outside the canonical route path."""
        return []

    def query_provider(self, query: str) -> DiscoveryResult:
        query_lower = query.lower().strip()
        for provider_id, info in self.CLOUD_PROVIDERS.items():
            if query_lower in (provider_id, info["name"].lower(), info["type"].lower()):
                return self._cloud_result(provider_id, info)

        if query_lower in {
            "ollama",
            "llamacpp",
            "llama.cpp",
            "vllm",
            "local",
            "local model",
            "on-premise",
            "self-hosted",
            "sovereign local model",
        }:
            return self._sovereign_local_result()

        if any(keyword in query_lower for keyword in ("api", "openai", "compatible", "endpoint")):
            return DiscoveryResult(
                provider_id="custom_openai",
                provider_name=f"Custom: {query}",
                provider_type="openai_text",
                status="discoverable",
                reason="Potential OpenAI-compatible capability requires a governed TV/TVC route",
                connection_method="tv_tvc",
                instructions=[
                    "Register endpoint metadata through the governed StegVerse route path.",
                    "Any credential must be resolved by TV/TVC; do not place provider secrets in this bridge.",
                    "Discovery does not grant route or execution authority.",
                ],
                config_template={
                    "name": "custom",
                    "type": "openai_text",
                    "enabled": False,
                    "credential_authority": "TV/TVC",
                    "route_authority": "StegVerse-Labs/TVC",
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
                "Add or consume a governed provider contract before use.",
            ],
            config_template={},
            requires_network=True,
            requires_api_key=True,
            estimated_cost_tier="unknown",
        )

    def _sovereign_local_result(self) -> DiscoveryResult:
        return DiscoveryResult(
            provider_id="stegverse_sovereign_local_model",
            provider_name="StegVerse Sovereign Local Model",
            provider_type="sovereign_local_model",
            status="machine_owned",
            reason="Implementation is complete/released; live route activation is owned by the sovereign heartbeat and TVC",
            connection_method="tvc_route",
            instructions=[
                "Canonical model/runtime: StegVerse-002/micro-node-runtime#22.",
                "Canonical live carrier: StegVerse-Labs/.github#60 / SHWP-DURABLE-RUNTIME-ACTIVATION.",
                "Canonical route task: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json.",
                "Transport: StegVerse-org/LLM-adapter#18; custody/reconstruction: master-records/orchestration.",
                "Credential requirement for the repository-local model is NONE; TV/TVC remains credential authority.",
                "This bridge must not launch, select, prove, or admit a competing local runtime.",
            ],
            config_template={
                "name": "stegverse-sovereign-local-model",
                "type": "sovereign_local_model",
                "enabled": False,
                "credential_authority": "TV/TVC",
                "credential_requirement": "NONE",
                "route_authority": "StegVerse-Labs/TVC",
                "canonical_model_owner": "StegVerse-002/micro-node-runtime#22",
                "machine_owned_activation": True,
            },
            requires_network=False,
            requires_api_key=False,
            estimated_cost_tier="free",
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
