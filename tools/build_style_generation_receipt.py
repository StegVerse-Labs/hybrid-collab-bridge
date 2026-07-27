#!/usr/bin/env python3
"""Build a governed style-generation receipt from prompt and output artifacts."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_payload(record: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in record.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model-family", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--platform-context", required=True)
    parser.add_argument("--revision", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    key = os.getenv("HCB_STYLE_RECEIPT_KEY")
    signer_id = os.getenv("HCB_STYLE_RECEIPT_SIGNER_ID", "")
    key_ref = os.getenv("HCB_STYLE_RECEIPT_KEY_REF", "")
    cryptographic = bool(key and signer_id and key_ref)

    record: dict[str, Any] = {
        "receipt_id": f"STYLE-RECEIPT-{args.sample_id}",
        "sample_id": args.sample_id,
        "provider": args.provider,
        "model_family": args.model_family,
        "model_version": args.model_version,
        "prompt_hash": sha256_file(args.prompt),
        "output_hash": sha256_file(args.output),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance_level": "cryptographically_bound" if cryptographic else "asserted",
        "human_revision": {
            "applied": args.revision is not None,
            "revision_hash": sha256_file(args.revision) if args.revision else None,
        },
        "platform_context": args.platform_context,
        "signature": {
            "algorithm": "hmac-sha256" if cryptographic else "none",
            "signer_id": signer_id if cryptographic else "",
            "key_ref": key_ref if cryptographic else "",
            "value": "",
        },
    }
    if cryptographic:
        record["signature"]["value"] = hmac.new(
            key.encode(), canonical_payload(record), hashlib.sha256
        ).hexdigest()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
