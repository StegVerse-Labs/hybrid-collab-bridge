#!/usr/bin/env python3
"""Independently verify a governed style-experiment evidence bundle.

Verification establishes integrity and reconstructability only. It never grants publication
or origin-attribution authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "stegverse.style-experiment-evidence-bundle.v1"
EXPECTED_MAXIMUM_CLAIM = "observed association between interaction and classifier reliability"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def safe_artifact(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError(f"invalid artifact path: {relative!r}")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"artifact escapes experiment root: {relative}") from exc
    if candidate.is_symlink():
        raise ValueError(f"symbolic links are not admissible evidence artifacts: {relative}")
    if not candidate.is_file():
        raise ValueError(f"artifact is missing or not a file: {relative}")
    return candidate


def verify_bundle(root: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    artifacts = manifest.get("artifacts")
    if manifest.get("schema") != EXPECTED_SCHEMA:
        errors.append("unsupported or missing evidence-bundle schema")
    if manifest.get("bundle_version") != 1:
        errors.append("unsupported bundle_version")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("manifest artifacts must be a non-empty list")
        artifacts = []

    claim = manifest.get("claim_boundary") or {}
    if claim.get("maximum_claim") != EXPECTED_MAXIMUM_CLAIM:
        errors.append("maximum claim boundary was changed")
    if claim.get("origin_attribution_prohibited") is not True:
        errors.append("origin attribution prohibition is not retained")
    if claim.get("causation_claim_prohibited") is not True:
        errors.append("causation claim prohibition is not retained")
    if manifest.get("publication_admissible") is not False:
        errors.append("evidence integrity cannot grant publication authority")

    seen: set[str] = set()
    verified: list[dict[str, Any]] = []
    for row in artifacts:
        if not isinstance(row, dict):
            errors.append("artifact inventory contains a non-object entry")
            continue
        relative = row.get("path")
        if not isinstance(relative, str):
            errors.append("artifact inventory entry has no valid path")
            continue
        if relative in seen:
            errors.append(f"duplicate artifact inventory path: {relative}")
            continue
        seen.add(relative)
        try:
            path = safe_artifact(root, relative)
            data = path.read_bytes()
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        actual_hash = sha256_bytes(data)
        actual_size = len(data)
        if row.get("sha256") != actual_hash:
            errors.append(f"artifact hash mismatch: {relative}")
        if row.get("size_bytes") != actual_size:
            errors.append(f"artifact size mismatch: {relative}")
        verified.append({"path": relative, "sha256": actual_hash, "size_bytes": actual_size})

    canonical_inventory = sorted(
        [
            {"path": row.get("path"), "sha256": row.get("sha256"), "size_bytes": row.get("size_bytes")}
            for row in artifacts
            if isinstance(row, dict)
        ],
        key=lambda row: str(row.get("path")),
    )
    expected_inventory_hash = sha256_bytes(canonical_json(canonical_inventory))
    if manifest.get("inventory_sha256") != expected_inventory_hash:
        errors.append("inventory hash mismatch")

    required = {"packet.json", "readiness-report.json", "execution-plan.json"}
    missing_required = sorted(required - seen)
    if missing_required:
        errors.append("required artifacts missing from inventory: " + ", ".join(missing_required))

    experiment_ids: dict[str, Any] = {}
    for name in sorted(required & seen):
        try:
            value = json.loads((root / name).read_text(encoding="utf-8"))
            experiment_ids[name] = value.get("experiment_id")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"{name} cannot be reconstructed as JSON: {exc}")
    declared_id = manifest.get("experiment_id")
    for name, experiment_id in experiment_ids.items():
        if experiment_id != declared_id:
            errors.append(f"experiment_id mismatch in {name}")

    report = {
        "schema": "stegverse.style-experiment-evidence-verification.v1",
        "experiment_id": declared_id,
        "status": "VERIFIED" if not errors else "INVALID",
        "integrity_verified": not errors,
        "reconstructability_verified": not errors,
        "publication_admissible": False,
        "verified_artifact_count": len(verified),
        "verified_artifacts": sorted(verified, key=lambda row: row["path"]),
        "claim_boundary": {
            "maximum_claim": EXPECTED_MAXIMUM_CLAIM,
            "origin_attribution_prohibited": True,
            "causation_claim_prohibited": True,
        },
        "errors": errors,
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_root")
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.experiment_root)
    manifest_path = safe_artifact(root, args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report, errors = verify_bundle(root, manifest)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = (root / args.output).resolve()
        try:
            output.relative_to(root.resolve())
        except ValueError as exc:
            raise SystemExit(f"output escapes experiment root: {args.output}") from exc
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
