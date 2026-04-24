from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Task:
    task_type: str
    prompt: str
    options: Dict[str, Any]
