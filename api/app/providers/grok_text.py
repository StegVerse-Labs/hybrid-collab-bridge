"""xAI Grok text provider.

Uses OpenAI-compatible API at api.x.ai/v1.
Grok 4.1 Fast is the recommended model for 2026 (2M context, fast, cheap).
"""
import os
from typing import Dict, Any
from .openai_text import OpenAIText
from ..tasks import Task


class GrokText(OpenAIText):
    """xAI Grok provider. OpenAI-compatible endpoint."""

    def __init__(self, name: str):
        super().__init__(
            name,
            api_key_env="XAI_API_KEY",
            base_url_env="XAI_BASE",
            model_env="XAI_MODEL",
            default_model="grok-4-1-fast-reasoning",
        )
        self.type = "grok_text"
