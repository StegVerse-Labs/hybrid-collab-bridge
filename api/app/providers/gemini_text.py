"""Google Gemini external text provider compatibility surface.

Direct provider credentials and direct network execution are prohibited in the
bridge consumer. Use an admitted TV/TVC provider-operation route.
"""
import os
from typing import Dict, Any

from ..tasks import Task
from .base import Provider


BLOCKED_REASON = "TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED"


class GeminiText(Provider):
    def __init__(self, name: str):
        super().__init__(name, "gemini_text", ["text-generate"])
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def run(self, task: Task) -> Dict[str, Any]:
        if task.task_type != "text-generate":
            return {"error": "unsupported task"}
        return {
            "state": "BLOCKED",
            "error": BLOCKED_REASON,
            "provider": self.name,
            "provider_type": self.type,
            "credential_material_present": False,
            "provider_execution_performed": False,
            "authority_effect": False,
        }
