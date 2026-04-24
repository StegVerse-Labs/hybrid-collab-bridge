"""OpenAI-compatible text provider.

Supports any provider using the OpenAI chat completions API format:
- OpenAI (GPT-4, GPT-4o, o3, etc.)
- Moonshot AI / Kimi (via OpenAI-compatible endpoint)
- xAI / Grok (via OpenAI-compatible endpoint)
- Any other OpenAI-compatible service
"""
import os
import httpx
from typing import Dict, Any
from ..tasks import Task
from .base import Provider


class OpenAIText(Provider):
    """OpenAI-compatible text generation provider."""

    def __init__(self, name: str, api_key_env: str = "OPENAI_API_KEY",
                 base_url_env: str = "OPENAI_BASE", model_env: str = "OPENAI_MODEL",
                 default_model: str = "gpt-4o"):
        super().__init__(name, "openai_text", ["text-generate"])
        self.api_key_env = api_key_env
        self.base_url_env = base_url_env
        self.model_env = model_env
        self.default_model = default_model

        key = os.getenv(api_key_env)
        if not key:
            raise RuntimeError(f"{api_key_env} missing")

        self.api_key = key
        self.base_url = os.getenv(base_url_env, "https://api.openai.com/v1")
        self.model = os.getenv(model_env, default_model)
        self.headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def run(self, task: Task) -> Dict[str, Any]:
        if task.task_type != "text-generate":
            return {"error": "unsupported task"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": task.prompt}],
            "max_tokens": 1200,
            "temperature": task.options.get("temperature", 0.4),
        }

        timeout = float(os.getenv("HTTP_TIMEOUT", "60"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"].get("content", "")
            return {"text": content.strip()}
