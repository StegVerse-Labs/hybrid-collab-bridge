from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_CONDITIONS = {
    "same_access_no_trajectory",
    "partial_trajectory",
    "full_trajectory",
    "human_only_control",
    "shared_source_control",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify(packet: Path) -> tuple[dict, list[str]]:
    errors: list[str] = []
    manifest_path = packet / "packet-manifest.json"
    receipt_path = packet / "initialization-receipt.json"
    if not manifest_path.is_file():
        return {}, ["missing packet-manifest.json"]
    if not receipt_path.is_file():
        return {}, ["missing initialization-receipt.json"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    declared_manifest_hash = manifest.pop("manifest_sha256", None)
    if declared_manifest_hash != canonical_hash(manifest):
        errors.append("manifest canonical hash mismatch")
    manifest["manifest_sha256"] = declared_manifest_hash

    if receipt.get("packet_manifest_sha256") != sha256_file(manifest_path):
        errors.append("receipt manifest file hash mismatch")
    receipt_copy = dict(receipt)
    declared_receipt_hash = receipt_copy.pop("receipt_sha256", None)
    if declared_receipt_hash != canonical_hash(receipt_copy):
        errors.append("initialization receipt hash mismatch")

    for label in ("source", "prompt", "trajectory"):
        entry = manifest.get("inputs", {}).get(label)
        if not entry:
            errors.append(f"missing input declaration: {label}")
            continue
        path = packet / entry["path"]
        if not path.is_file():
            errors.append(f"missing input file: {entry['path']}")
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256"):
            errors.append(f"input hash mismatch: {label}")
        if actual != receipt.get("input_hashes", {}).get(label):
            errors.append(f"receipt input hash mismatch: {label}")

    condition_entries = manifest.get("conditions", [])
    conditions = {entry.get("condition") for entry in condition_entries}
    missing = REQUIRED_CONDITIONS - conditions
    extra = conditions - REQUIRED_CONDITIONS
    if missing:
        errors.append(f"missing conditions: {sorted(missing)}")
    if extra:
        errors.append(f"unexpected conditions: {sorted(extra)}")

    participant_slots: list[str] = []
    evaluator_slots: list[str] = []
    for entry in condition_entries:
        participant_slots.extend(entry.get("participant_slots", []))
        evaluator_slots.extend(entry.get("evaluator_slots", []))
        observation_path = packet / entry.get("observation_path", "")
        if not observation_path.is_file():
            errors.append(f"missing observation file: {entry.get('observation_path')}")
    if len(participant_slots) != len(set(participant_slots)):
        errors.append("participant slot collision")
    if len(evaluator_slots) != len(set(evaluator_slots)):
        errors.append("evaluator slot collision")
    if set(participant_slots) & set(evaluator_slots):
        errors.append("participant/evaluator identity collision")

    result_path = packet / manifest.get("result_path", "result/experiment.json")
    result_state = "PENDING"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("source_packet_hash") != manifest["inputs"]["source"]["sha256"]:
            errors.append("result source hash is not bound to packet")
        if result.get("prompt_hash") != manifest["inputs"]["prompt"]["sha256"]:
            errors.append("result prompt hash is not bound to packet")
        if result.get("trajectory_packet_hash") != manifest["inputs"]["trajectory"]["sha256"]:
            errors.append("result trajectory hash is not bound to packet")
        result_state = "BOUND" if not errors else "INVALID"

    report = {
        "experiment_id": manifest.get("experiment_id"),
        "packet_status": "FAILED" if errors else "COMPLETE",
        "result_state": result_state,
        "verified_conditions": sorted(conditions & REQUIRED_CONDITIONS),
        "errors": errors,
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    report, errors = verify(args.packet)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
