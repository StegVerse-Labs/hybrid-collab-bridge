from __future__ import annotations
import json
import time
import uuid
from pathlib import Path
from .hashing import digest_object

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "state" / "ledger.jsonl"
RECEIPT_PATH = ROOT / "meta" / "receipts" / "latest_receipt.json"


def _last_hash() -> str | None:
    if not LEDGER_PATH.exists():
        return None
    lines = LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return None
    last = json.loads(lines[-1])
    return last["entry_hash"]


def append_ledger_entry(
    mutation_class: str,
    actor: str,
    payload: dict,
    bcat: dict,
    gcat: dict,
) -> dict:
    entry = {
        "entry_id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "mutation_class": mutation_class,
        "actor": actor,
        "payload": payload,
        "prev_hash": _last_hash(),
        "bcat": bcat,
        "gcat": gcat,
    }
    entry["entry_hash"] = digest_object(entry)
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    receipt = {
        "receipt_id": str(uuid.uuid4()),
        "ledger_entry_id": entry["entry_id"],
        "entry_hash": entry["entry_hash"],
        "prev_hash": entry["prev_hash"],
        "mutation_class": mutation_class,
        "actor": actor,
        "decision": "admitted",
        "timestamp": entry["timestamp"],
        "bcat": bcat,
        "gcat": gcat,
    }
    receipt["receipt_hash"] = digest_object(receipt)
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    return receipt
