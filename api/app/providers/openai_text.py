"""OpenAI-compatible external text provider.

Credential-bearing execution is intentionally disabled in this consumer repo.
An already-admitted TV/TVC provider-operation route must perform any external
provider call and return only bounded non-secret output/evidence.
"""
import os
from typing import Dict, Any

from ..tasks import Task
from .base import Provider


BLOCKED_REASON = "TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED"


class OpenAIText(Provider):
    """Fail-closed OpenAI-compatible provider placeholder."""

    def __init__(
        self,
        name: str,
        base_url_env: str = "OPENAI_BASE",
        model_env: str = "OPENAI_MODEL",
        default_model: str = "gpt-4o",
    ):
        super().__init__(name, "openai_text", ["text-generate"])
        self.base_url = os.getenv(base_url_env, "https://api.openai.com/v1")
        self.model = os.getenv(model_env, default_model)

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
