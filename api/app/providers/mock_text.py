from ..tasks import Task
from .base import Provider
from .disposition import unsupported_task

class MockText(Provider):
    def __init__(self, name: str):
        super().__init__(name, "mock_text", ["text-generate"])

    async def run(self, task: Task):
        if task.task_type != "text-generate":
            return unsupported_task(self, task.task_type)
        snippet = (task.prompt or "")[:120]
        if len(task.prompt or "") > 120:
            snippet += "..."
        return {"text": f"MOCK({self.name}): {snippet}"}
