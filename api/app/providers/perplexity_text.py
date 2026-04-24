"""Perplexity text provider.

Search-augmented generation. Every response includes citations.
Uses OpenAI-compatible API at api.perplexity.ai.
"""
import os
from typing import Dict, Any
from .openai_text import OpenAIText
from ..tasks import Task


class PerplexityText(OpenAIText):
    """Perplexity provider. Search-augmented, OpenAI-compatible endpoint."""

    def __init__(self, name: str):
        super().__init__(
            name,
            api_key_env="PERPLEXITY_API_KEY",
            base_url_env="PERPLEXITY_BASE",
            model_env="PERPLEXITY_MODEL",
            default_model="sonar-pro",
        )
        self.type = "perplexity_text"
