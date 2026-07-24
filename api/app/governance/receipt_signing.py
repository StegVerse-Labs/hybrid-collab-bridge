"""Receipt signing and independent verification.

HMAC-SHA256 is the initial deployable signer contract. The secret is never
persisted. Receipts carry only signer identity, key reference, algorithm, and
signature. The interface is deliberately small so an asymmetric/KMS-backed
implementation can replace it without changing the receipt evidence contract.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any


ALGORITHM = "HMAC-SHA256"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class ReceiptSigner:
    signer_id: str
    key_ref: str
    secret: bytes
    algorithm: str = ALGORITHM

    @classmethod
    def from_environment(cls, required: bool = True) -> "ReceiptSigner | None":
        secret = os.getenv("HCB_RECEIPT_SIGNING_KEY", "")
        if not secret:
            if required:
                raise ValueError("HCB_RECEIPT_SIGNING_KEY is required for mediated receipt signing")
            return None
        signer_id = os.getenv("HCB_RECEIPT_SIGNER_ID", "human-llm-pair-assessor")
        key_ref = os.getenv("HCB_RECEIPT_SIGNING_KEY_REF", "env:HCB_RECEIPT_SIGNING_KEY")
        if not signer_id.strip():
            raise ValueError("HCB_RECEIPT_SIGNER_ID must not be empty")
        if not key_ref.strip():
            raise ValueError("HCB_RECEIPT_SIGNING_KEY_REF must not be empty")
        return cls(signer_id=signer_id, key_ref=key_ref, secret=secret.encode("utf-8"))

    def sign(self, payload: dict[str, Any]) -> dict[str, str]:
        signed = {
            **payload,
            "signer_id": self.signer_id,
            "key_ref": self.key_ref,
            "signature_algorithm": self.algorithm,
        }
        signature = hmac.new(self.secret, canonical_bytes(signed), hashlib.sha256).hexdigest()
        return {
            "signer_id": self.signer_id,
            "key_ref": self.key_ref,
            "signature_algorithm": self.algorithm,
            "signature": signature,
        }

    def verify(self, receipt: dict[str, Any]) -> bool:
        if receipt.get("signer_id") != self.signer_id:
            return False
        if receipt.get("key_ref") != self.key_ref:
            return False
        if receipt.get("signature_algorithm") != self.algorithm:
            return False
        signature = receipt.get("signature")
        if not isinstance(signature, str) or not signature:
            return False
        signed = {key: value for key, value in receipt.items() if key != "signature"}
        expected = hmac.new(self.secret, canonical_bytes(signed), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)


def verification_metadata(receipt: dict[str, Any], signer: ReceiptSigner) -> dict[str, Any]:
    return {
        "verified": signer.verify(receipt),
        "signer_id": receipt.get("signer_id"),
        "key_ref": receipt.get("key_ref"),
        "signature_algorithm": receipt.get("signature_algorithm"),
    }
