"""DeepSeek text provider.

Uses OpenAI-compatible API at api.deepseek.com/v1.
DeepSeek-V3 for general tasks, DeepSeek-R1 for reasoning.
"""
import os
from typing import Dict, Any
from .openai_text import OpenAIText
from ..tasks import Task


class DeepSeekText(OpenAIText):
    """DeepSeek provider. OpenAI-compatible endpoint."""

    def __init__(self, name: str):
        super().__init__(
            name,
            api_key_env="DEEPSEEK_API_KEY",
            base_url_env="DEEPSEEK_BASE",
            model_env="DEEPSEEK_MODEL",
            default_model="deepseek-chat",
        )
        self.type = "deepseek_text"
