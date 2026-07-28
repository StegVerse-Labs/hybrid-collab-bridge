#!/usr/bin/env python3
"""Build a canonical, hash-bound evidence manifest for a governed style experiment.

The builder does not grant publication authority. It binds existing experiment artifacts
into a deterministic manifest so another observer can verify the exact evidence set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_ARTIFACTS = (
    "packet.json",
    "readiness-report.json",
    "execution-plan.json",
)
OPTIONAL_ARTIFACTS = (
    "baseline-report.json",
    "followup-report.json",
    "accommodation-report.json",
    "degradation-report.json",
    "governed-summary.json",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def safe_file(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"artifact escapes experiment root: {relative}") from exc
    if candidate.is_symlink():
        raise ValueError(f"symbolic links are not admissible evidence artifacts: {relative}")
    if not candidate.is_file():
        raise ValueError(f"artifact is missing or not a file: {relative}")
    return candidate


def build_manifest(root: Path, include_optional: bool = True) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    artifacts: list[dict[str, Any]] = []

    packet_path = root / "packet.json"
    experiment_id = None
    if packet_path.is_file():
        try:
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            experiment_id = packet.get("experiment_id")
        except json.JSONDecodeError as exc:
            errors.append(f"packet.json is invalid JSON: {exc}")

    names = list(REQUIRED_ARTIFACTS)
    if include_optional:
        names.extend(name for name in OPTIONAL_ARTIFACTS if (root / name).is_file())

    for relative in names:
        try:
            path = safe_file(root, relative)
            data = path.read_bytes()
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        artifacts.append({
            "path": relative,
            "sha256": sha256_bytes(data),
            "size_bytes": len(data),
        })

    artifacts.sort(key=lambda row: row["path"])
    inventory_hash = sha256_bytes(canonical_json(artifacts))
    manifest = {
        "schema": "stegverse.style-experiment-evidence-bundle.v1",
        "bundle_version": 1,
        "experiment_id": experiment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETE" if not errors else "BLOCKED",
        "verification_admissible": not errors,
        "publication_admissible": False,
        "claim_boundary": {
            "maximum_claim": "observed association between interaction and classifier reliability",
            "origin_attribution_prohibited": True,
            "causation_claim_prohibited": True,
        },
        "artifacts": artifacts,
        "inventory_sha256": inventory_hash,
        "errors": errors,
    }
    return manifest, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_root")
    parser.add_argument("--output", default="manifest.json")
    parser.add_argument("--required-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.experiment_root)
    manifest, errors = build_manifest(root, include_optional=not args.required_only)
    output = safe_output(root, args.output)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 1 if errors else 0


def safe_output(root: Path, relative: str) -> Path:
    output = (root / relative).resolve()
    try:
        output.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"output escapes experiment root: {relative}") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


if __name__ == "__main__":
    raise SystemExit(main())
