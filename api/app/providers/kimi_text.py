"""Moonshot/Kimi external provider compatibility surface."""
from .openai_text import OpenAIText


class KimiText(OpenAIText):
    def __init__(self, name: str):
        super().__init__(
            name,
            base_url_env="MOONSHOT_BASE",
            model_env="MOONSHOT_MODEL",
            default_model="kimi-k2.6",
        )
        self.type = "kimi_text"
