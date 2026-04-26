import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cge_light"))

from cge.hashing import digest_object
from cge.ingest import ingest_object
from cge.policy import evaluate_bcat, evaluate_gcat
from cge.ledger import append_ledger_entry
from cge.receipts import verify_receipt

class TestCGELight:
    def test_digest_deterministic(self):
        obj = {"a": 1, "b": 2}
        h1 = digest_object(obj)
        h2 = digest_object(obj)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_ingest_basic(self):
        obj = {"test": True}
        result = ingest_object(obj, "test_source")
        assert result["ingested"] is True
        assert result["source"] == "test_source"
        assert "payload_hash" in result

    def test_bcat_evaluation(self):
        obj = {"content": "test"}
        result = ingest_object(obj)
        bcat = evaluate_bcat(result)
        assert 0 <= bcat["observability"] <= 1
        assert 0 <= bcat["risk"] <= 1
        assert bcat["observability"] > bcat["risk"]  # Test payload should score well

    def test_gcat_normalization(self):
        obj = {"content": "test"}
        result = ingest_object(obj)
        bcat = evaluate_bcat(result)
        gcat = evaluate_gcat(bcat)
        total = sum(gcat.values())
        assert abs(total - 1.0) < 0.01
        assert all(0 <= v <= 1 for v in gcat.values())

    def test_ledger_append_and_verify(self):
        obj = {"test": "ledger"}
        result = ingest_object(obj)
        bcat = evaluate_bcat(result)
        gcat = evaluate_gcat(bcat)

        receipt = append_ledger_entry("test", "actor_1", obj, bcat, gcat)
        assert "receipt_id" in receipt
        assert "entry_hash" in receipt
        assert verify_receipt(receipt) is True

    def test_receipt_tamper_detection(self):
        obj = {"test": "tamper"}
        result = ingest_object(obj)
        bcat = evaluate_bcat(result)
        gcat = evaluate_gcat(bcat)

        receipt = append_ledger_entry("test", "actor_1", obj, bcat, gcat)
        receipt["actor"] = "EVIL_ACTOR"
        assert verify_receipt(receipt) is False
