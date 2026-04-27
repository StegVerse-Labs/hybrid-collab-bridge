"""Custom Provider Adapter Template.

For providers discovered via the "other" path that are OpenAI-compatible
or require custom integration.

Copy this file, rename, and modify the API calls to match your provider.
"""
from __future__ import annotations
import os
import httpx
from typing import Dict, Any
from ..tasks import Task
from .base import Provider


class CustomProviderTemplate(Provider):
    """Template for custom AI provider integration.

    Instructions:
    1. Copy this file to your_provider_name.py
    2. Rename the class
    3. Set the appropriate env var names
    4. Modify the API endpoint and payload format
    5. Register in registry.py FACTORY dict
    6. Add entry to providers.txt
    """

    def __init__(self, name: str):
        super().__init__(name, "custom_provider", ["text-generate"])

        # --- CONFIGURATION: Set your env vars ---
        self.api_key_env = "YOUR_PROVIDER_API_KEY"
        self.base_url_env = "YOUR_PROVIDER_BASE"
        self.model_env = "YOUR_PROVIDER_MODEL"
        self.default_model = "your-default-model"

        # --- Load configuration ---
        key = os.getenv(self.api_key_env)
        if not key:
            raise RuntimeError(f"{self.api_key_env} missing")

        self.api_key = key
        self.base_url = os.getenv(self.base_url_env, "https://api.your-provider.com/v1")
        self.model = os.getenv(self.model_env, self.default_model)

        # --- Headers: Modify for your provider's auth scheme ---
        self.headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def run(self, task: Task) -> Dict[str, Any]:
        if task.task_type != "text-generate":
            return {"error": "unsupported task"}

        # --- PAYLOAD: Modify for your provider's API format ---
        # OpenAI-compatible format (most common):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": task.prompt}],
            "max_tokens": 1200,
            "temperature": task.options.get("temperature", 0.4),
        }

        # --- Alternative formats (uncomment if needed) ---
        # # Anthropic format:
        # payload = {
        #     "model": self.model,
        #     "messages": [{"role": "user", "content": task.prompt}],
        #     "max_tokens": 1200,
        # }
        # 
        # # Google Gemini format:
        # payload = {
        #     "contents": [{"parts": [{"text": task.prompt}]}],
        #     "generationConfig": {
        #         "temperature": task.options.get("temperature", 0.4),
        #     },
        # }

        timeout = float(os.getenv("HTTP_TIMEOUT", "60"))

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # --- ENDPOINT: Modify for your provider ---
                r = await client.post(
                    f"{self.base_url}/chat/completions",  # OpenAI-compatible
                    # f"{self.base_url}/v1/messages",      # Anthropic
                    # f"{self.base_url}/models/{self.model}:generateContent",  # Gemini
                    headers=self.headers,
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()

                # --- RESPONSE PARSING: Modify for your provider ---
                # OpenAI-compatible:
                content = data["choices"][0]["message"].get("content", "")

                # Anthropic:
                # pieces = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
                # content = "\n".join(pieces)

                # Gemini:
                # content = data["candidates"][0]["content"]["parts"][0].get("text", "")

                return {"text": content.strip()}

        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}
