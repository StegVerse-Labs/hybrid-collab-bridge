"""Ollama local text provider.

Runs entirely on-premise. No API key, no network dependency.
Pull models via: ollama pull llama3.2, ollama pull mistral, ollama pull phi4
"""
import os
import httpx
from typing import Dict, Any
from ..tasks import Task
from .base import Provider
from .disposition import provider_unreachable, unsupported_task


class OllamaText(Provider):
    """Ollama local inference provider."""

    def __init__(self, name: str):
        super().__init__(name, "ollama_text", ["text-generate"])
        self.base_url = os.getenv("OLLAMA_BASE", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "120"))

    async def run(self, task: Task) -> Dict[str, Any]:
        if task.task_type != "text-generate":
            return unsupported_task(self, task.task_type)

        payload = {
            "model": self.model,
            "prompt": task.prompt,
            "stream": False,
            "options": {
                "temperature": task.options.get("temperature", 0.4),
                "num_predict": 1200,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
                return {"text": data.get("response", "").strip()}
        except httpx.ConnectError:
            return provider_unreachable(
                self, f"Ollama not reachable at {self.base_url}", self.base_url
            )
        except Exception as e:
            return provider_unreachable(self, str(e), self.base_url)
