from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

CONDITIONS = [
    "same_access_no_trajectory",
    "partial_trajectory",
    "full_trajectory",
    "human_only_control",
    "shared_source_control",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def initialize(experiment_id: str, source: Path, prompt: Path, trajectory: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty packet directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    inputs = output / "inputs"
    observations = output / "observations"
    inputs.mkdir()
    observations.mkdir()

    copied = {}
    for label, original in (("source", source), ("prompt", prompt), ("trajectory", trajectory)):
        if not original.is_file():
            raise FileNotFoundError(original)
        destination = inputs / f"{label}{original.suffix or '.txt'}"
        shutil.copyfile(original, destination)
        copied[label] = {
            "path": destination.relative_to(output).as_posix(),
            "sha256": sha256_file(destination),
        }

    assignments = []
    for index, condition in enumerate(CONDITIONS, start=1):
        assignments.append({
            "condition": condition,
            "participant_slots": [f"{condition}-participant-{n}" for n in (1, 2)],
            "evaluator_slots": [f"{condition}-evaluator-{n}" for n in (1, 2)],
            "observation_path": f"observations/{condition}.jsonl",
        })
        (observations / f"{condition}.jsonl").write_text("", encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "experiment_id": experiment_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "INITIALIZED",
        "inputs": copied,
        "conditions": assignments,
        "required_observations_per_condition": 2,
        "result_path": "result/experiment.json",
    }
    manifest["manifest_sha256"] = canonical_hash(manifest)
    (output / "packet-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "receipt_type": "attribution_trajectory_packet_initialization",
        "experiment_id": experiment_id,
        "packet_manifest_sha256": sha256_file(output / "packet-manifest.json"),
        "input_hashes": {key: value["sha256"] for key, value in copied.items()},
        "status": "COMPLETE",
    }
    receipt["receipt_sha256"] = canonical_hash(receipt)
    (output / "initialization-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--trajectory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    initialize(args.experiment_id, args.source, args.prompt, args.trajectory, args.output)
    print(args.output / "packet-manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
