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
        self.reload()

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
            try:
                self.providers[name] = cls(name)
            except RuntimeError as e:
                print(f"[registry] Skipping {name}: {e}")
                continue

    def get(self, name: str) -> Provider | None:
        return self.providers.get(name)

    def list(self) -> List[str]:
        return list(self.providers.keys())
