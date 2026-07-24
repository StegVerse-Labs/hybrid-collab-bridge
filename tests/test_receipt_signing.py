import json
from pathlib import Path

import pytest

from api.app.governance.human_llm_evidence import (
    GENESIS_HASH,
    build_mediated_receipts,
    persist_mediated_receipts,
    verify_mediated_chain,
)
from api.app.governance.receipt_signing import ReceiptSigner


def _signer(secret: bytes = b"test-secret") -> ReceiptSigner:
    return ReceiptSigner(
        signer_id="test-assessor",
        key_ref="test:key:1",
        secret=secret,
    )


def _record():
    return {
        "assessment_id": "assessment-signing-1",
        "trace_id": "trace-signing-1",
        "timestamp": "2026-07-24T12:00:00Z",
        "mediated_composition": {
            "claimed_level": "governed_composition",
            "local_admissibility": [
                {
                    "participant_id": "model-a",
                    "decision": "allow",
                    "policy_ref": "policy:a",
                    "evidence": ["evidence:a"],
                    "receipt_ref": "declared:a",
                },
                {
                    "participant_id": "human-h",
                    "decision": "allow",
                    "policy_ref": "policy:h",
                    "evidence": ["evidence:h"],
                    "receipt_ref": "declared:h",
                },
                {
                    "participant_id": "model-b",
                    "decision": "allow",
                    "policy_ref": "policy:b",
                    "evidence": ["evidence:b"],
                    "receipt_ref": "declared:b",
                },
            ],
        },
    }


def test_signed_chain_verifies():
    signer = _signer()
    receipts, head = build_mediated_receipts(_record(), signer=signer)
    result = verify_mediated_chain(receipts, signer)
    assert result["verified"] is True
    assert result["count"] == 3
    assert result["genesis_hash"] == GENESIS_HASH
    assert result["chain_head"] == head
    assert all(item["verified"] for item in result["results"])


def test_wrong_key_fails_verification():
    receipts, _ = build_mediated_receipts(_record(), signer=_signer())
    result = verify_mediated_chain(receipts, _signer(b"wrong-secret"))
    assert result["verified"] is False
    assert any(not item["verified"] for item in result["results"])


def test_payload_mutation_fails_hash_and_signature():
    signer = _signer()
    receipts, _ = build_mediated_receipts(_record(), signer=signer)
    receipts[1]["decision"] = "deny"
    result = verify_mediated_chain(receipts, signer)
    assert result["verified"] is False
    assert result["results"][1]["hash_verified"] is False


def test_chain_reordering_fails_sequence_or_previous_hash():
    signer = _signer()
    receipts, _ = build_mediated_receipts(_record(), signer=signer)
    receipts[0], receipts[1] = receipts[1], receipts[0]
    result = verify_mediated_chain(receipts, signer)
    assert result["verified"] is False
    assert any(not item["previous_hash_verified"] for item in result["results"])


def test_missing_environment_key_fails_closed(monkeypatch):
    monkeypatch.delenv("HCB_RECEIPT_SIGNING_KEY", raising=False)
    with pytest.raises(ValueError, match="HCB_RECEIPT_SIGNING_KEY"):
        build_mediated_receipts(_record())


def test_persistence_writes_receipts_and_verification(tmp_path: Path):
    summary = persist_mediated_receipts(_record(), tmp_path, signer=_signer())
    assert summary is not None
    assert summary["signatures_verified"] is True
    assert summary["signer_id"] == "test-assessor"
    assert summary["key_ref"] == "test:key:1"
    receipt_path = Path(summary["path"])
    verification_path = Path(summary["verification_path"])
    assert receipt_path.exists()
    assert verification_path.exists()
    receipts = [json.loads(line) for line in receipt_path.read_text().splitlines()]
    verification = json.loads(verification_path.read_text())
    assert len(receipts) == 3
    assert all(receipt["signature"] for receipt in receipts)
    assert verification["verified"] is True
