"""Canonical StegVerse local-runtime discovery, launch planning, and proof.

This module is intentionally credential-free.  It discovers only loopback local
inference runtimes and never reads provider API keys.  Runtime availability is
not execution authority; callers must separately traverse the canonical
StegGate/admissibility path before any governed consequence.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Optional

import httpx

PROOF_SCHEMA = "stegverse.local-runtime-proof.v1"
MODEL_PROFILE_SCHEMA = "stegverse.local-model-profile.v1"


@dataclass(frozen=True)
class RuntimeSpec:
    runtime_id: str
    display_name: str
    probe_url: str
    models_url: str
    executable: str
    launch_argv: tuple[str, ...]
    provider_type: str


RUNTIME_SPECS: tuple[RuntimeSpec, ...] = (
    RuntimeSpec(
        runtime_id="ollama",
        display_name="Ollama",
        probe_url="http://127.0.0.1:11434/api/tags",
        models_url="http://127.0.0.1:11434/api/tags",
        executable="ollama",
        launch_argv=("ollama", "serve"),
        provider_type="ollama_text",
    ),
    RuntimeSpec(
        runtime_id="llamacpp",
        display_name="llama.cpp",
        probe_url="http://127.0.0.1:8080/v1/models",
        models_url="http://127.0.0.1:8080/v1/models",
        executable="llama-server",
        launch_argv=("llama-server",),
        provider_type="openai_compatible_local",
    ),
    RuntimeSpec(
        runtime_id="vllm",
        display_name="vLLM",
        probe_url="http://127.0.0.1:8000/v1/models",
        models_url="http://127.0.0.1:8000/v1/models",
        executable="vllm",
        launch_argv=("vllm", "serve"),
        provider_type="openai_compatible_local",
    ),
)


@dataclass
class LocalModel:
    name: str
    digest: Optional[str] = None
    size_bytes: Optional[int] = None
    modified_at: Optional[str] = None


@dataclass
class RuntimeObservation:
    runtime_id: str
    display_name: str
    endpoint: str
    provider_type: str
    status: str
    http_status: Optional[int]
    latency_ms: Optional[float]
    executable_present: bool
    models: list[LocalModel] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class LaunchPlan:
    runtime_id: str
    executable_present: bool
    argv: list[str]
    safe_to_auto_launch: bool
    reason: str


@dataclass
class LocalModelProfile:
    schema: str
    runtime_id: str
    endpoint: str
    model_name: str
    model_digest: Optional[str]
    capabilities: list[str]
    credential_required: bool
    identity_hash: str


@dataclass
class LocalRuntimeProof:
    schema: str
    observed_at: str
    runtime_id: str
    endpoint: str
    http_status: int
    latency_ms: float
    model_profile: LocalModelProfile
    credential_material_present: bool
    runtime_ready: bool
    proof_hash: str


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _parse_models(runtime_id: str, payload: Mapping[str, Any]) -> list[LocalModel]:
    models: list[LocalModel] = []
    if runtime_id == "ollama":
        for raw in payload.get("models", []) or []:
            if not isinstance(raw, Mapping):
                continue
            name = str(raw.get("name") or raw.get("model") or "").strip()
            if not name:
                continue
            models.append(
                LocalModel(
                    name=name,
                    digest=str(raw.get("digest")) if raw.get("digest") else None,
                    size_bytes=int(raw["size"]) if isinstance(raw.get("size"), int) else None,
                    modified_at=str(raw.get("modified_at")) if raw.get("modified_at") else None,
                )
            )
        return models

    for raw in payload.get("data", []) or []:
        if not isinstance(raw, Mapping):
            continue
        name = str(raw.get("id") or "").strip()
        if name:
            models.append(LocalModel(name=name))
    return models


def choose_model(models: Iterable[LocalModel], preferred: Optional[str] = None) -> Optional[LocalModel]:
    ordered = sorted(models, key=lambda model: model.name)
    if preferred:
        for model in ordered:
            if model.name == preferred:
                return model
        return None
    return ordered[0] if ordered else None


class LocalRuntimeManager:
    """Credential-free manager for loopback inference runtimes."""

    def __init__(
        self,
        specs: Iterable[RuntimeSpec] = RUNTIME_SPECS,
        command_finder: Callable[[str], Optional[str]] = shutil.which,
        client_factory: Optional[Callable[[], httpx.AsyncClient]] = None,
    ) -> None:
        self.specs = tuple(specs)
        self.command_finder = command_finder
        self.client_factory = client_factory or (
            lambda: httpx.AsyncClient(timeout=httpx.Timeout(2.0), follow_redirects=False)
        )

    def launch_plan(self, runtime_id: str) -> LaunchPlan:
        spec = self._spec(runtime_id)
        executable_present = bool(self.command_finder(spec.executable))
        # Ollama has a complete no-model-argument server launch. llama.cpp and
        # vLLM require a model/config choice, so auto-launch remains fail-closed.
        safe = runtime_id == "ollama" and executable_present
        if safe:
            reason = "bounded credential-free launch command available"
        elif not executable_present:
            reason = f"runtime executable not found: {spec.executable}"
        else:
            reason = "runtime requires explicit model/config arguments; auto-launch denied"
        return LaunchPlan(
            runtime_id=runtime_id,
            executable_present=executable_present,
            argv=list(spec.launch_argv),
            safe_to_auto_launch=safe,
            reason=reason,
        )

    def launch(self, runtime_id: str) -> subprocess.Popen[Any]:
        plan = self.launch_plan(runtime_id)
        if not plan.safe_to_auto_launch:
            raise RuntimeError(plan.reason)
        return subprocess.Popen(  # noqa: S603 - argv is fixed by RuntimeSpec
            plan.argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            shell=False,
        )

    async def discover(self) -> list[RuntimeObservation]:
        observations: list[RuntimeObservation] = []
        async with self.client_factory() as client:
            for spec in self.specs:
                observations.append(await self._observe(client, spec))
        return observations

    async def prove(
        self,
        runtime_id: str,
        preferred_model: Optional[str] = None,
    ) -> LocalRuntimeProof:
        spec = self._spec(runtime_id)
        async with self.client_factory() as client:
            observation = await self._observe(client, spec)
        if observation.status != "ready" or observation.http_status != 200:
            raise RuntimeError(observation.error or f"{runtime_id} is not ready")
        selected = choose_model(observation.models, preferred_model)
        if selected is None:
            raise RuntimeError("runtime is reachable but no admissible local model is available")

        profile_body = {
            "schema": MODEL_PROFILE_SCHEMA,
            "runtime_id": runtime_id,
            "endpoint": spec.probe_url,
            "model_name": selected.name,
            "model_digest": selected.digest,
            "capabilities": ["text-generate", "local-inference"],
            "credential_required": False,
        }
        profile = LocalModelProfile(
            **profile_body,
            identity_hash=_sha256(profile_body),
        )
        proof_body = {
            "schema": PROOF_SCHEMA,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "runtime_id": runtime_id,
            "endpoint": spec.probe_url,
            "http_status": int(observation.http_status),
            "latency_ms": float(observation.latency_ms or 0.0),
            "model_profile": asdict(profile),
            "credential_material_present": False,
            "runtime_ready": True,
        }
        return LocalRuntimeProof(**proof_body, proof_hash=_sha256(proof_body))

    @staticmethod
    def validate_proof(proof: LocalRuntimeProof) -> bool:
        if proof.schema != PROOF_SCHEMA:
            return False
        if proof.credential_material_present or not proof.runtime_ready:
            return False
        if proof.http_status != 200 or proof.model_profile.credential_required:
            return False
        profile_body = asdict(proof.model_profile)
        identity_hash = profile_body.pop("identity_hash")
        if _sha256(profile_body) != identity_hash:
            return False
        proof_body = asdict(proof)
        proof_hash = proof_body.pop("proof_hash")
        return _sha256(proof_body) == proof_hash

    async def _observe(self, client: httpx.AsyncClient, spec: RuntimeSpec) -> RuntimeObservation:
        start = time.perf_counter()
        executable_present = bool(self.command_finder(spec.executable))
        try:
            response = await client.get(spec.models_url)
            latency_ms = round((time.perf_counter() - start) * 1000.0, 3)
            if response.status_code != 200:
                return RuntimeObservation(
                    runtime_id=spec.runtime_id,
                    display_name=spec.display_name,
                    endpoint=spec.probe_url,
                    provider_type=spec.provider_type,
                    status="unavailable",
                    http_status=response.status_code,
                    latency_ms=latency_ms,
                    executable_present=executable_present,
                    error=f"unexpected HTTP status {response.status_code}",
                )
            try:
                payload = response.json()
            except ValueError as exc:
                return RuntimeObservation(
                    runtime_id=spec.runtime_id,
                    display_name=spec.display_name,
                    endpoint=spec.probe_url,
                    provider_type=spec.provider_type,
                    status="unavailable",
                    http_status=response.status_code,
                    latency_ms=latency_ms,
                    executable_present=executable_present,
                    error=f"invalid model inventory JSON: {exc}",
                )
            models = _parse_models(spec.runtime_id, payload)
            return RuntimeObservation(
                runtime_id=spec.runtime_id,
                display_name=spec.display_name,
                endpoint=spec.probe_url,
                provider_type=spec.provider_type,
                status="ready" if models else "reachable_no_models",
                http_status=response.status_code,
                latency_ms=latency_ms,
                executable_present=executable_present,
                models=models,
                error=None if models else "runtime reachable but model inventory is empty",
            )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            return RuntimeObservation(
                runtime_id=spec.runtime_id,
                display_name=spec.display_name,
                endpoint=spec.probe_url,
                provider_type=spec.provider_type,
                status="unavailable",
                http_status=None,
                latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
                executable_present=executable_present,
                error=type(exc).__name__,
            )

    def _spec(self, runtime_id: str) -> RuntimeSpec:
        for spec in self.specs:
            if spec.runtime_id == runtime_id:
                return spec
        raise KeyError(f"unsupported local runtime: {runtime_id}")
