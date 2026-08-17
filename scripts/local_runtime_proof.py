#!/usr/bin/env python3
"""Discover, optionally launch, and prove a StegVerse local inference runtime."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api"
if str(API) not in sys.path:
    sys.path.insert(0, str(API))

from app.providers.local_runtime import LocalRuntimeManager  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=["ollama", "llamacpp", "vllm"])
    parser.add_argument("--model", help="Exact local model name to prove")
    parser.add_argument("--launch", action="store_true", help="Launch only when the canonical bounded launch plan permits it")
    parser.add_argument("--dry-run", action="store_true", help="Print discovery and launch plans without claiming activation")
    parser.add_argument("--receipt", type=Path, help="Write successful proof receipt JSON to this path")
    parser.add_argument("--launch-wait-seconds", type=float, default=15.0)
    return parser


async def _wait_for_runtime(manager: LocalRuntimeManager, runtime_id: str, seconds: float) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + seconds
    while loop.time() < deadline:
        observations = await manager.discover()
        observation = next(item for item in observations if item.runtime_id == runtime_id)
        if observation.status == "ready":
            return
        await asyncio.sleep(0.5)
    raise RuntimeError(f"{runtime_id} did not become ready within {seconds} seconds")


async def _run(args: argparse.Namespace) -> int:
    manager = LocalRuntimeManager()
    observations = await manager.discover()
    launch_plans = {item.runtime_id: asdict(manager.launch_plan(item.runtime_id)) for item in observations}

    if args.dry_run:
        print(json.dumps({
            "mode": "DRY_RUN_NO_ACTIVATION_CLAIM",
            "observations": [asdict(item) for item in observations],
            "launch_plans": launch_plans,
        }, indent=2, sort_keys=True))
        return 0

    runtime_id = args.runtime
    if runtime_id is None:
        ready = [item for item in observations if item.status == "ready"]
        if len(ready) != 1:
            print(json.dumps({
                "status": "REVIEW_REQUIRED",
                "reason": "specify --runtime unless exactly one supported runtime is ready",
                "ready_runtimes": [item.runtime_id for item in ready],
            }, indent=2, sort_keys=True), file=sys.stderr)
            return 2
        runtime_id = ready[0].runtime_id

    selected = next(item for item in observations if item.runtime_id == runtime_id)
    if selected.status != "ready" and args.launch:
        manager.launch(runtime_id)
        await _wait_for_runtime(manager, runtime_id, args.launch_wait_seconds)
    elif selected.status != "ready":
        print(json.dumps({
            "status": "BLOCKED",
            "runtime": runtime_id,
            "reason": selected.error or selected.status,
            "launch_plan": launch_plans[runtime_id],
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 3

    try:
        proof = await manager.prove(runtime_id, args.model)
    except RuntimeError as exc:
        print(json.dumps({
            "status": "FAILED",
            "runtime": runtime_id,
            "reason": str(exc),
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 4

    if not manager.validate_proof(proof):
        print(json.dumps({
            "status": "FAILED",
            "runtime": runtime_id,
            "reason": "generated proof did not validate",
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 5

    payload = asdict(proof)
    payload["status"] = "COMPLETE"
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


def main() -> int:
    return asyncio.run(_run(_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
