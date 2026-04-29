import os
import yaml
from typing import Dict, List
from .providers.base import Provider
from .providers.anthropic_text import AnthropicText
from .providers.openai_text import OpenAIText
from .providers.kimi_text import KimiText
from .providers.gemini_text import GeminiText
from .providers.grok_text import GrokText
from .providers.deepseek_text import DeepSeekText
from .providers.perplexity_text import PerplexityText
from .providers.ollama_text import OllamaText
from .providers.mock_text import MockText

# TVC integration (optional, loaded if available)
try:
    from .governance.tv_tvc import TVCClient, TVProviderAdapter
    TVC_AVAILABLE = True
except ImportError:
    TVC_AVAILABLE = False

FACTORY = {
    "anthropic_text": AnthropicText,
    "openai_text": OpenAIText,
    "kimi_text": KimiText,
    "gemini_text": GeminiText,
    "grok_text": GrokText,
    "deepseek_text": DeepSeekText,
    "perplexity_text": PerplexityText,
    "ollama_text": OllamaText,
    "mock_text": MockText,
}

class ProviderRegistry:
    def __init__(self, cfg_path: str = "providers.txt"):
        self.cfg_path = cfg_path
        self.providers: Dict[str, Provider] = {}
        self.tvc = self._init_tvc()
        self.reload()

    def _init_tvc(self) -> TVCClient | None:
        """Initialize TVC if configured."""
        if not TVC_AVAILABLE:
            return None
        tvc_mode = os.getenv("TVC_MODE", "")
        if tvc_mode not in ["direct", "file", "env", "callback"]:
            return None
        return TVCClient(
            mode=tvc_mode,
            default_ttl=int(os.getenv("TVC_TTL", "3600")),
        )

    def reload(self):
        with open(self.cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self.providers = {}
        for p in cfg.get("providers", []):
            if not p.get("enabled", True):
                continue
            typ = p["type"]; name = p["name"]
            cls = FACTORY.get(typ)
            if not cls:
                continue

            credential_id = p.get("credential_id")

            try:
                base_provider = cls(name)

                # Wrap with TVC if credential_id specified and TVC available
                if credential_id and self.tvc and TVC_AVAILABLE:
                    self.providers[name] = TVProviderAdapter(
                        base_provider=base_provider,
                        tvc_client=self.tvc,
                        credential_id=credential_id,
                    )
                    print(f"[registry] {name} wrapped with TVC ({credential_id})")
                else:
                    self.providers[name] = base_provider

            except RuntimeError as e:
                # API key missing — try TVC fallback if available
                if credential_id and self.tvc and TVC_AVAILABLE:
                    try:
                        base_provider = cls.__new__(cls)
                        base_provider.name = name
                        base_provider.type = typ
                        base_provider.capabilities = p.get("capabilities", ["text-generate"])
                        self.providers[name] = TVProviderAdapter(
                            base_provider=base_provider,
                            tvc_client=self.tvc,
                            credential_id=credential_id,
                        )
                        print(f"[registry] {name} TVC fallback activated")
                    except Exception:
                        print(f"[registry] Skipping {name}: {e}")
                else:
                    print(f"[registry] Skipping {name}: {e}")
                continue

    def get(self, name: str) -> Provider | None:
        return self.providers.get(name)

    def list(self) -> List[str]:
        return list(self.providers.keys())
