#!/usr/bin/env python3
"""Build and verify authenticated mediated-composition receipt chains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from api.app.governance.human_llm_evidence import (
    GENESIS_HASH,
    build_mediated_receipts,
    canonical_json,
    verify_mediated_chain,
)
from api.app.governance.receipt_signing import ReceiptSigner


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


def build_file(input_path: Path, output_path: Path, verification_path: Path | None = None) -> int:
    signer = ReceiptSigner.from_environment(required=True)
    assert signer is not None
    all_receipts: list[dict[str, Any]] = []
    chain_hash = GENESIS_HASH
    for record in iter_records(input_path):
        receipts, chain_hash = build_mediated_receipts(record, chain_hash, signer=signer)
        all_receipts.extend(receipts)

    verification = verify_mediated_chain(all_receipts, signer)
    if all_receipts and not verification["verified"]:
        raise ValueError("generated receipt chain failed authentication or continuity verification")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for receipt in all_receipts:
            handle.write(canonical_json(receipt) + "\n")

    verify_path = verification_path or output_path.with_suffix(output_path.suffix + ".verification.json")
    verify_path.parent.mkdir(parents=True, exist_ok=True)
    verify_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(
        f"WROTE: {len(all_receipts)} authenticated receipts; "
        f"head={chain_hash}; verified={verification['verified']}; verification={verify_path}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Assessment JSONL input")
    parser.add_argument("output", type=Path, help="Authenticated receipt JSONL output")
    parser.add_argument("--verification", type=Path, help="Optional verification report path")
    args = parser.parse_args()
    try:
        return build_file(args.input, args.output, args.verification)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
