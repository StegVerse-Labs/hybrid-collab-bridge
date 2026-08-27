"""DeepSeek external provider compatibility surface."""
from .openai_text import OpenAIText


class DeepSeekText(OpenAIText):
    def __init__(self, name: str):
        super().__init__(
            name,
            base_url_env="DEEPSEEK_BASE",
            model_env="DEEPSEEK_MODEL",
            default_model="deepseek-chat",
        )
        self.type = "deepseek_text"
