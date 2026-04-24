from __future__ import annotations
from .hashing import digest_object


def verify_receipt(receipt: dict) -> bool:
    receipt_copy = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    expected = digest_object(receipt_copy)
    return receipt.get("receipt_hash") == expected
