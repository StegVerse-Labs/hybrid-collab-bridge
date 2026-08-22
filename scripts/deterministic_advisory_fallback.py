#!/usr/bin/env python3
"""Deterministic, non-authorizing fallback for legacy model-backed PR checks.

This deliberately performs no external model call and consumes no provider secret.
It preserves a useful PR check while model-backed review is routed through a future
StegVerse-native / TV-TVC-admitted execution surface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SUSPICIOUS_MARKERS = (
    "models.github.ai",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "STEGVERSE_AI_ENTITY_TOKEN",
    "gh auth login --with-token",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--context", default="context.diff")
    parser.add_argument("--summary", default="advisory-fallback.md")
    parser.add_argument("--receipt", default="advisory-fallback.json")
    args = parser.parse_args()

    path = Path(args.context)
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    findings = [marker for marker in SUSPICIOUS_MARKERS if marker in text]

    summary = [
        f"# {args.label} deterministic advisory fallback",
        "",
        "Provider-backed review is not executed by this compatibility check.",
        "The retired/unadmitted provider surface is durably separated from PR admission.",
        "",
        f"- context_sha256: `{digest}`",
        f"- context_bytes: `{len(text.encode('utf-8'))}`",
        "- authority_effect: `NONE`",
        "- fallback_mode: `PERSIST_BLOCKER_AND_CONTINUE`",
        "- model_backed_review: `BLOCKED_PENDING_STEGVERSE_NATIVE_OR_TV_TVC_ADMISSION`",
        "- provider_credentials_consumed: `false`",
        "- repository_mutation_from_model_output: `false`",
        "",
        "## Deterministic marker observations",
    ]
    if findings:
        summary.extend(f"- observed changed-context marker: `{item}`" for item in findings)
    else:
        summary.append("- none of the legacy provider/auth markers were observed in the bounded context")
    Path(args.summary).write_text("\n".join(summary) + "\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.hybrid_collab_bridge.deterministic_advisory_fallback.v1",
        "label": args.label,
        "context_sha256": digest,
        "context_bytes": len(text.encode("utf-8")),
        "legacy_markers_observed": findings,
        "authority_effect": "NONE",
        "fallback_mode": "PERSIST_BLOCKER_AND_CONTINUE",
        "model_backed_review": "BLOCKED_PENDING_STEGVERSE_NATIVE_OR_TV_TVC_ADMISSION",
        "provider_credentials_consumed": False,
        "external_provider_called": False,
        "repository_mutation_from_model_output": False,
    }
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(Path(args.summary).read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
