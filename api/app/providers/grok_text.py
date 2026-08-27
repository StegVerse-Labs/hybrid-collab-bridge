"""xAI Grok external provider compatibility surface."""
from .openai_text import OpenAIText


class GrokText(OpenAIText):
    def __init__(self, name: str):
        super().__init__(
            name,
            base_url_env="XAI_BASE",
            model_env="XAI_MODEL",
            default_model="grok-4-1-fast-reasoning",
        )
        self.type = "grok_text"
