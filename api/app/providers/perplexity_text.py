"""Perplexity external provider compatibility surface."""
from .openai_text import OpenAIText


class PerplexityText(OpenAIText):
    def __init__(self, name: str):
        super().__init__(
            name,
            base_url_env="PERPLEXITY_BASE",
            model_env="PERPLEXITY_MODEL",
            default_model="sonar-pro",
        )
        self.type = "perplexity_text"
