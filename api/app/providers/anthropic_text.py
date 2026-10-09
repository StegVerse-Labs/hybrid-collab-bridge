"""Anthropic external text provider compatibility surface.

Direct provider credentials and direct network execution are prohibited in the
bridge consumer. Use an admitted TV/TVC provider-operation route.
"""
import os
from typing import Dict, Any

from ..tasks import Task
from .base import Provider
from .disposition import admitted_route_required, unsupported_task


BLOCKED_REASON = "TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED"


class AnthropicText(Provider):
    def __init__(self, name: str):
        super().__init__(name, "anthropic_text", ["text-generate"])
        self.base_url = os.getenv("ANTHROPIC_BASE", "https://api.anthropic.com")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    async def run(self, task: Task) -> Dict[str, Any]:
        if task.task_type != "text-generate":
            return unsupported_task(self, task.task_type)
        return admitted_route_required(self, BLOCKED_REASON)
