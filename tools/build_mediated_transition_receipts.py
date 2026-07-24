#!/usr/bin/env python3
"""Build deterministic, hash-chained receipts for mediated composition assessments."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

GENESIS_HASH = "0" * 64


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def iter_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: record must be an object")
            yield record


def build_receipts(record: dict[str, Any], previous_hash: str = GENESIS_HASH) -> tuple[list[dict[str, Any]], str]:
    mediated = record.get("mediated_composition")
    if not isinstance(mediated, dict):
        return [], previous_hash

    assessment_id = record.get("assessment_id")
    trace_id = record.get("trace_id")
    timestamp = record.get("timestamp")
    local = mediated.get("local_admissibility", [])
    if not all(isinstance(item, dict) for item in local):
        raise ValueError(f"{assessment_id}: local_admissibility entries must be objects")

    receipts: list[dict[str, Any]] = []
    chain_hash = previous_hash
    assessment_hash = sha256_json(record)
    for sequence, decision in enumerate(local, start=1):
        payload = {
            "receipt_type": "mediated_local_admissibility",
            "assessment_id": assessment_id,
            "trace_id": trace_id,
            "timestamp": timestamp,
            "sequence": sequence,
            "participant_id": decision.get("participant_id"),
            "decision": decision.get("decision"),
            "policy_ref": decision.get("policy_ref"),
            "evidence": decision.get("evidence", []),
            "declared_receipt_ref": decision.get("receipt_ref"),
            "claimed_level": mediated.get("claimed_level"),
            "assessment_hash": assessment_hash,
            "previous_hash": chain_hash,
        }
        receipt_hash = sha256_json(payload)
        receipt = {**payload, "receipt_hash": receipt_hash}
        receipts.append(receipt)
        chain_hash = receipt_hash
    return receipts, chain_hash


def build_file(input_path: Path, output_path: Path) -> int:
    all_receipts: list[dict[str, Any]] = []
    chain_hash = GENESIS_HASH
    for record in iter_records(input_path):
        receipts, chain_hash = build_receipts(record, chain_hash)
        all_receipts.extend(receipts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for receipt in all_receipts:
            handle.write(canonical_json(receipt) + "\n")
    print(f"WROTE: {len(all_receipts)} receipts; head={chain_hash}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Assessment JSONL input")
    parser.add_argument("output", type=Path, help="Receipt JSONL output")
    args = parser.parse_args()
    try:
        return build_file(args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
