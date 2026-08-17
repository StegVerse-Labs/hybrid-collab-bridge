"""Formal, credential-free development contract for a StegVerse local model.

The builder never downloads a base model. It will only derive a StegVerse model
from a base model that is already present in the local Ollama inventory. This
keeps model acquisition outside this control surface and prevents a source or CI
run from pretending that a physical local model exists.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from .local_runtime import LocalModel

MODEL_DEFINITION_SCHEMA = "stegverse.local-model-definition.v1"
MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")

STEGVERSE_LOCAL_SYSTEM = """You are StegVerse Local, a local inference model operating behind StegVerse governance.
Produce candidate reasoning and candidate outputs only.
Do not claim execution authority, admissibility, approval, commitment, broadcast, signing, or external effect.
Preserve task identity and state references supplied by the caller.
When evidence is insufficient, state that it is insufficient rather than inventing authority or facts.
Secrets, tokens, and credential material are never required by this local model definition.
"""


@dataclass(frozen=True)
class LocalModelBuildPlan:
    schema: str
    base_model: str
    target_model: str
    system_prompt: str
    temperature: float
    definition_hash: str
    modelfile: str


@dataclass(frozen=True)
class LocalModelBuildReceipt:
    schema: str
    base_model: str
    target_model: str
    definition_hash: str
    executable: str
    exit_code: int
    built: bool


def _definition_hash(body: dict) -> str:
    rendered = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _valid_name(value: str) -> bool:
    return bool(MODEL_NAME_RE.fullmatch(value)) and ".." not in value


class LocalModelBuilder:
    def __init__(
        self,
        command_finder: Callable[[str], Optional[str]] = shutil.which,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.command_finder = command_finder
        self.runner = runner

    def plan(
        self,
        available_models: Iterable[LocalModel],
        base_model: str,
        target_model: str,
        temperature: float = 0.2,
    ) -> LocalModelBuildPlan:
        if not _valid_name(base_model) or not _valid_name(target_model):
            raise ValueError("base and target model names must use the bounded local-model name grammar")
        available = {model.name for model in available_models}
        if base_model not in available:
            raise RuntimeError("base model is not present in the local runtime inventory; download is not authorized here")
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        body = {
            "schema": MODEL_DEFINITION_SCHEMA,
            "base_model": base_model,
            "target_model": target_model,
            "system_prompt": STEGVERSE_LOCAL_SYSTEM,
            "temperature": temperature,
        }
        definition_hash = _definition_hash(body)
        escaped_system = STEGVERSE_LOCAL_SYSTEM.replace('"""', '\"\"\"')
        modelfile = (
            f"FROM {base_model}\n"
            f"PARAMETER temperature {temperature}\n"
            f"SYSTEM \"\"\"{escaped_system}\"\"\"\n"
        )
        return LocalModelBuildPlan(
            **body,
            definition_hash=definition_hash,
            modelfile=modelfile,
        )

    def build(self, plan: LocalModelBuildPlan) -> LocalModelBuildReceipt:
        executable = self.command_finder("ollama")
        if not executable:
            raise RuntimeError("ollama executable is not available; local model build is blocked")

        with tempfile.TemporaryDirectory(prefix="stegverse-local-model-") as directory:
            path = Path(directory) / "Modelfile"
            path.write_text(plan.modelfile, encoding="utf-8")
            completed = self.runner(
                [executable, "create", plan.target_model, "-f", str(path)],
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
                shell=False,
            )
        return LocalModelBuildReceipt(
            schema=MODEL_DEFINITION_SCHEMA,
            base_model=plan.base_model,
            target_model=plan.target_model,
            definition_hash=plan.definition_hash,
            executable=executable,
            exit_code=int(completed.returncode),
            built=completed.returncode == 0,
        )
