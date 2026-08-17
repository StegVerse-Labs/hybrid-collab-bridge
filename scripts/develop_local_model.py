#!/usr/bin/env python3
"""Develop and prove a StegVerse local model from an installed Ollama base."""
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

from app.providers.local_model import LocalModelBuilder  # noqa: E402
from app.providers.local_runtime import LocalRuntimeManager  # noqa: E402


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-model", required=True, help="Exact model already present in Ollama inventory")
    p.add_argument("--target-model", default="stegverse-local:v1")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--plan-only", action="store_true", help="Validate and print the model definition without building")
    return p


async def run(args: argparse.Namespace) -> int:
    runtime = LocalRuntimeManager()
    observations = await runtime.discover()
    ollama = next(item for item in observations if item.runtime_id == "ollama")
    if ollama.status != "ready":
        print(json.dumps({
            "status": "BLOCKED",
            "owner": "physical-local-host",
            "release_condition": "Ollama loopback responds with a non-empty model inventory",
            "reason": ollama.error or ollama.status,
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 3

    builder = LocalModelBuilder()
    try:
        plan = builder.plan(
            ollama.models,
            base_model=args.base_model,
            target_model=args.target_model,
            temperature=args.temperature,
        )
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 4

    if args.plan_only:
        payload = asdict(plan)
        payload["status"] = "PLAN_VALID_NO_BUILD_CLAIM"
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    build_receipt = builder.build(plan)
    if not build_receipt.built:
        print(json.dumps({"status": "FAILED", "build": asdict(build_receipt)}, indent=2, sort_keys=True), file=sys.stderr)
        return 5

    try:
        proof = await runtime.prove("ollama", args.target_model)
    except RuntimeError as exc:
        print(json.dumps({
            "status": "FAILED",
            "build": asdict(build_receipt),
            "reason": f"model build returned success but post-build proof failed: {exc}",
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 6

    if not runtime.validate_proof(proof):
        print(json.dumps({"status": "FAILED", "reason": "post-build proof failed validation"}, indent=2), file=sys.stderr)
        return 7

    payload = {
        "status": "COMPLETE",
        "model_development": asdict(build_receipt),
        "runtime_proof": asdict(proof),
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


def main() -> int:
    return asyncio.run(run(parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
