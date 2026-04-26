"""StegVerse Provider Discovery Engine.

Searches for available AI ecosystems, validates access, and guides users
through connection. Part of the StegVerse "any protocol, any scenario"
communication philosophy.

Discovery methods (in order of preference):
1. Local scan — Ollama, llama.cpp, vLLM running on localhost
2. Environment scan — API keys in env vars
3. Network scan — well-known endpoints on local network
4. Registry query — StegVerse provider registry (future)
5. Manual entry — user provides connection details
"""
from __future__ import annotations
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import httpx


@dataclass
class DiscoveryResult:
    """Result of a provider discovery attempt."""
    provider_id: str
    provider_name: str
    provider_type: str
    status: str  # "available" | "unavailable" | "discoverable" | "denied"
    reason: str
    connection_method: str  # "local" | "env" | "network" | "manual" | "none"
    instructions: List[str] = field(default_factory=list)
    config_template: Dict[str, Any] = field(default_factory=dict)
    requires_network: bool = True
    requires_api_key: bool = True
    estimated_cost_tier: str = "unknown"  # "free" | "cheap" | "standard" | "premium"


class ProviderDiscoveryEngine:
    """Discovers and validates AI provider access."""

    # Well-known local endpoints to probe
    LOCAL_ENDPOINTS = {
        "ollama": {"url": "http://localhost:11434/api/tags", "method": "GET"},
        "ollama_alt": {"url": "http://127.0.0.1:11434/api/tags", "method": "GET"},
        "vllm": {"url": "http://localhost:8000/v1/models", "method": "GET"},
        "llamacpp": {"url": "http://localhost:8080/tokenize", "method": "POST"},
        "textgen": {"url": "http://localhost:5000/v1/models", "method": "GET"},
    }

    # Known cloud providers with connection templates
    CLOUD_PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "type": "openai_text",
            "env_key": "OPENAI_API_KEY",
            "base_url_env": "OPENAI_BASE",
            "default_base": "https://api.openai.com/v1",
            "signup_url": "https://platform.openai.com/signup",
            "pricing_url": "https://openai.com/pricing",
            "cost_tier": "premium",
            "docs_url": "https://platform.openai.com/docs",
        },
        "anthropic": {
            "name": "Anthropic (Claude)",
            "type": "anthropic_text",
            "env_key": "ANTHROPIC_API_KEY",
            "base_url_env": "ANTHROPIC_BASE",
            "default_base": "https://api.anthropic.com",
            "signup_url": "https://console.anthropic.com",
            "pricing_url": "https://www.anthropic.com/pricing",
            "cost_tier": "premium",
            "docs_url": "https://docs.anthropic.com",
        },
        "moonshot": {
            "name": "Moonshot AI (Kimi)",
            "type": "kimi_text",
            "env_key": "MOONSHOT_API_KEY",
            "base_url_env": "MOONSHOT_BASE",
            "default_base": "https://api.moonshot.ai/v1",
            "signup_url": "https://platform.moonshot.ai",
            "pricing_url": "https://platform.moonshot.ai/pricing",
            "cost_tier": "standard",
            "docs_url": "https://platform.moonshot.ai/docs",
        },
        "google": {
            "name": "Google (Gemini)",
            "type": "gemini_text",
            "env_key": "GEMINI_API_KEY",
            "base_url_env": None,
            "default_base": None,
            "signup_url": "https://aistudio.google.com/app/apikey",
            "pricing_url": "https://ai.google.dev/pricing",
            "cost_tier": "cheap",
            "docs_url": "https://ai.google.dev/gemini-api/docs",
        },
        "xai": {
            "name": "xAI (Grok)",
            "type": "grok_text",
            "env_key": "XAI_API_KEY",
            "base_url_env": "XAI_BASE",
            "default_base": "https://api.x.ai/v1",
            "signup_url": "https://console.x.ai",
            "pricing_url": "https://x.ai/pricing",
            "cost_tier": "standard",
            "docs_url": "https://docs.x.ai",
        },
        "deepseek": {
            "name": "DeepSeek",
            "type": "deepseek_text",
            "env_key": "DEEPSEEK_API_KEY",
            "base_url_env": "DEEPSEEK_BASE",
            "default_base": "https://api.deepseek.com/v1",
            "signup_url": "https://platform.deepseek.com",
            "pricing_url": "https://platform.deepseek.com/pricing",
            "cost_tier": "cheap",
            "docs_url": "https://platform.deepseek.com/docs",
        },
        "perplexity": {
            "name": "Perplexity",
            "type": "perplexity_text",
            "env_key": "PERPLEXITY_API_KEY",
            "base_url_env": "PERPLEXITY_BASE",
            "default_base": "https://api.perplexity.ai",
            "signup_url": "https://www.perplexity.ai/settings/api",
            "pricing_url": "https://www.perplexity.ai/pricing",
            "cost_tier": "standard",
            "docs_url": "https://docs.perplexity.ai",
        },
    }

    def __init__(self):
        self.discovered: List[DiscoveryResult] = []

    async def scan_all(self) -> List[DiscoveryResult]:
        """Full discovery scan: local + env + network."""
        results = []
        results.extend(await self.scan_local())
        results.extend(await self.scan_environment())
        results.extend(await self.scan_network())
        self.discovered = results
        return results

    async def scan_local(self) -> List[DiscoveryResult]:
        """Scan for locally running inference servers."""
        results = []
        for provider_id, endpoint in self.LOCAL_ENDPOINTS.items():
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    if endpoint["method"] == "GET":
                        r = await client.get(endpoint["url"])
                    else:
                        r = await client.post(endpoint["url"], json={"content": "test"})
                    if r.status_code in (200, 401):
                        # 401 means server is there but needs auth (still available)
                        results.append(DiscoveryResult(
                            provider_id=provider_id,
                            provider_name=self._local_name(provider_id),
                            provider_type="ollama_text" if "ollama" in provider_id else "custom",
                            status="available",
                            reason=f"Local server responding at {endpoint['url']}",
                            connection_method="local",
                            instructions=[
                                "Local server detected. No API key needed.",
                                f"Endpoint: {endpoint['url']}",
                                "Add to providers.txt to enable.",
                            ],
                            config_template={
                                "name": provider_id,
                                "type": "ollama_text" if "ollama" in provider_id else "custom",
                                "enabled": True,
                                "capabilities": ["text-generate"],
                            },
                            requires_network=False,
                            requires_api_key=False,
                            estimated_cost_tier="free",
                        ))
            except (httpx.ConnectError, httpx.TimeoutException):
                pass  # Not running, skip silently
        return results

    async def scan_environment(self) -> List[DiscoveryResult]:
        """Scan environment variables for configured API keys."""
        results = []
        for provider_id, info in self.CLOUD_PROVIDERS.items():
            env_key = info["env_key"]
            if os.getenv(env_key):
                # Key exists — provider is available
                results.append(DiscoveryResult(
                    provider_id=provider_id,
                    provider_name=info["name"],
                    provider_type=info["type"],
                    status="available",
                    reason=f"API key found in {env_key}",
                    connection_method="env",
                    instructions=[
                        f"API key detected: {env_key}",
                        "Provider is ready to use.",
                        f"Verify at: {info['docs_url']}",
                    ],
                    config_template={
                        "name": provider_id,
                        "type": info["type"],
                        "enabled": True,
                        "capabilities": ["text-generate"],
                    },
                    requires_network=True,
                    requires_api_key=True,
                    estimated_cost_tier=info["cost_tier"],
                ))
            else:
                # Key missing — provider is discoverable but needs setup
                results.append(DiscoveryResult(
                    provider_id=provider_id,
                    provider_name=info["name"],
                    provider_type=info["type"],
                    status="discoverable",
                    reason=f"API key not found: {env_key}",
                    connection_method="manual",
                    instructions=[
                        f"1. Sign up: {info['signup_url']}",
                        f"2. Get API key and set env var: {env_key}=your-key",
                        f"3. (Optional) Set base URL: {info['base_url_env']}={info['default_base']}" if info["base_url_env"] else "3. No base URL needed",
                        f"4. Check pricing: {info['pricing_url']}",
                        f"5. Documentation: {info['docs_url']}",
                    ],
                    config_template={
                        "name": provider_id,
                        "type": info["type"],
                        "enabled": True,
                        "capabilities": ["text-generate"],
                    },
                    requires_network=True,
                    requires_api_key=True,
                    estimated_cost_tier=info["cost_tier"],
                ))
        return results

    async def scan_network(self) -> List[DiscoveryResult]:
        """Scan local network for inference servers."""
        results = []
        # Common local network IPs to probe for Ollama/vLLM
        local_ips = ["192.168.1.{}".format(i) for i in range(1, 20)]
        local_ips += ["10.0.0.{}".format(i) for i in range(1, 20)]

        for ip in local_ips:
            try:
                url = f"http://{ip}:11434/api/tags"
                async with httpx.AsyncClient(timeout=2) as client:
                    r = await client.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        models = [m.get("name", "unknown") for m in data.get("models", [])]
                        results.append(DiscoveryResult(
                            provider_id=f"ollama_{ip.replace('.', '_')}",
                            provider_name=f"Ollama @ {ip}",
                            provider_type="ollama_text",
                            status="available",
                            reason=f"Ollama server found on network at {ip}",
                            connection_method="network",
                            instructions=[
                                f"Network Ollama detected at {ip}:11434",
                                f"Available models: {', '.join(models[:5])}",
                                f"Set OLLAMA_BASE=http://{ip}:11434 to connect",
                            ],
                            config_template={
                                "name": f"ollama-{ip}",
                                "type": "ollama_text",
                                "enabled": True,
                                "capabilities": ["text-generate"],
                            },
                            requires_network=True,
                            requires_api_key=False,
                            estimated_cost_tier="free",
                        ))
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
        return results

    def query_provider(self, query: str) -> DiscoveryResult:
        """Handle user query for a specific provider."""
        query_lower = query.lower().strip()

        # Check if it's a known provider
        for provider_id, info in self.CLOUD_PROVIDERS.items():
            if query_lower in [provider_id, info["name"].lower(), info["type"].lower()]:
                env_key = info["env_key"]
                has_key = bool(os.getenv(env_key))

                if has_key:
                    return DiscoveryResult(
                        provider_id=provider_id,
                        provider_name=info["name"],
                        provider_type=info["type"],
                        status="available",
                        reason=f"Configured and ready",
                        connection_method="env",
                        instructions=[
                            f"✓ {info['name']} is connected.",
                            f"API key: {env_key} is set.",
                            f"Use expert '{provider_id}' in your requests.",
                        ],
                        config_template={
                            "name": provider_id,
                            "type": info["type"],
                            "enabled": True,
                            "capabilities": ["text-generate"],
                        },
                        requires_network=True,
                        requires_api_key=True,
                        estimated_cost_tier=info["cost_tier"],
                    )
                else:
                    return DiscoveryResult(
                        provider_id=provider_id,
                        provider_name=info["name"],
                        provider_type=info["type"],
                        status="discoverable",
                        reason="Found but not configured",
                        connection_method="manual",
                        instructions=[
                            f"{info['name']} is supported but not yet connected.",
                            f"1. Sign up: {info['signup_url']}",
                            f"2. Get API key and set: {env_KEY}=your-key",
                            f"3. Pricing: {info['pricing_url']}",
                            f"4. Docs: {info['docs_url']}",
                        ],
                        config_template={
                            "name": provider_id,
                            "type": info["type"],
                            "enabled": True,
                            "capabilities": ["text-generate"],
                        },
                        requires_network=True,
                        requires_api_key=True,
                        estimated_cost_tier=info["cost_tier"],
                    )

        # Check for local providers
        if query_lower in ["ollama", "local", "on-premise", "self-hosted"]:
            return DiscoveryResult(
                provider_id="ollama",
                provider_name="Ollama (Local)",
                provider_type="ollama_text",
                status="discoverable",
                reason="Local inference option available",
                connection_method="local",
                instructions=[
                    "Ollama runs entirely on your machine — no network, no API key.",
                    "1. Install: curl -fsSL https://ollama.com/install.sh | sh",
                    "2. Pull a model: ollama pull llama3.2",
                    "3. Start server: ollama serve",
                    "4. Bridge auto-detects at http://localhost:11434",
                    "5. Set OLLAMA_MODEL=llama3.2 (or your chosen model)",
                ],
                config_template={
                    "name": "ollama",
                    "type": "ollama_text",
                    "enabled": True,
                    "capabilities": ["text-generate"],
                },
                requires_network=False,
                requires_api_key=False,
                estimated_cost_tier="free",
            )

        # Unknown provider — check if it might be OpenAI-compatible
        if any(kw in query_lower for kw in ["api", "openai", "compatible", "endpoint"]):
            return DiscoveryResult(
                provider_id="custom_openai",
                provider_name=f"Custom: {query}",
                provider_type="openai_text",
                status="discoverable",
                reason="Potentially OpenAI-compatible — manual configuration required",
                connection_method="manual",
                instructions=[
                    f"StegVerse does not recognize '{query}' as a known provider.",
                    "If it uses an OpenAI-compatible API, you can connect it manually:",
                    "1. Set CUSTOM_API_KEY=your-key",
                    "2. Set CUSTOM_BASE=https://api.provider.com/v1",
                    "3. Add entry to providers.txt with type: openai_text",
                    "4. Restart the bridge",
                    "",
                    "If it's not OpenAI-compatible, you can create a custom adapter:",
                    "1. Copy api/app/providers/openai_text.py to custom_provider.py",
                    "2. Modify the API calls to match the provider's format",
                    "3. Register in registry.py",
                ],
                config_template={
                    "name": "custom",
                    "type": "openai_text",
                    "enabled": False,
                    "capabilities": ["text-generate"],
                },
                requires_network=True,
                requires_api_key=True,
                estimated_cost_tier="unknown",
            )

        # Truly unknown — denied with explanation
        return DiscoveryResult(
            provider_id="unknown",
            provider_name=query,
            provider_type="unknown",
            status="denied",
            reason="Provider not recognized and no compatibility path identified",
            connection_method="none",
            instructions=[
                f"'{query}' is not a known AI provider in the StegVerse ecosystem.",
                "",
                "Possible reasons:",
                "- The provider may not have a public API",
                "- The provider may use a proprietary protocol StegVerse cannot interface with",
                "- The provider name may be misspelled",
                "- The provider may be too new and not yet integrated",
                "",
                "Options:",
                "1. Check if the provider offers an OpenAI-compatible API — if so, use 'openai_text' adapter",
                "2. Request integration via StegVerse governance (human+AI quorum)",
                "3. Build a custom adapter (see docs for provider development)",
                "4. Use an alternative provider from the supported list",
                "",
                "Supported providers: OpenAI, Anthropic, Kimi, Gemini, Grok, DeepSeek, Perplexity, Ollama",
            ],
            config_template={},
            requires_network=True,
            requires_api_key=True,
            estimated_cost_tier="unknown",
        )

    def _local_name(self, provider_id: str) -> str:
        names = {
            "ollama": "Ollama (localhost)",
            "ollama_alt": "Ollama (127.0.0.1)",
            "vllm": "vLLM Server",
            "llamacpp": "llama.cpp Server",
            "textgen": "Text Generation WebUI",
        }
        return names.get(provider_id, provider_id)
