"""Google Gemini text provider.

Uses the Google GenAI SDK (google-generativeai).
Gemini 2.5 Pro / Flash recommended for 2026.
"""
import os
from typing import Dict, Any
from ..tasks import Task
from .base import Provider


class GeminiText(Provider):
    """Google Gemini provider."""

    def __init__(self, name: str):
        super().__init__(name, "gemini_text", ["text-generate"])
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing")
        self.api_key = key
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def run(self, task: Task) -> Dict[str, Any]:
        if task.task_type != "text-generate":
            return {"error": "unsupported task"}

        try:
            import google.generativeai as genai
        except ImportError:
            return {"error": "google-generativeai not installed. Run: pip install google-generativeai"}

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        # Gemini uses generate_content, not chat.completions
        response = model.generate_content(
            task.prompt,
            generation_config={
                "temperature": task.options.get("temperature", 0.4),
                "max_output_tokens": 1200,
            }
        )
        return {"text": response.text.strip()}
