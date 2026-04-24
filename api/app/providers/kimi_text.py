"""Moonshot AI Kimi text provider.

Uses OpenAI-compatible API at api.moonshot.ai/v1.
Kimi K2.6 is the flagship model as of April 2026.
"""
import os
from typing import Dict, Any
from .openai_text import OpenAIText
from ..tasks import Task


class KimiText(OpenAIText):
    """Moonshot AI Kimi provider. OpenAI-compatible endpoint."""

    def __init__(self, name: str):
        super().__init__(
            name,
            api_key_env="MOONSHOT_API_KEY",
            base_url_env="MOONSHOT_BASE",
            model_env="MOONSHOT_MODEL",
            default_model="kimi-k2.6",
        )
        self.type = "kimi_text"
        # Kimi K2.6 recommended temperatures: 1.0 for thinking mode, 0.6 for instant mode
        # We default to 0.6 for concise bridge outputs
