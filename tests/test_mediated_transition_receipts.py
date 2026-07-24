import copy
import unittest

from api.app.governance.human_llm_evidence import (
    GENESIS_HASH,
    build_mediated_receipts,
    sha256_json,
    verify_mediated_chain,
)
from api.app.governance.receipt_signing import ReceiptSigner


class MediatedTransitionReceiptTests(unittest.TestCase):
    def setUp(self):
        self.signer = ReceiptSigner(
            signer_id="test-assessor",
            key_ref="test:key:mediated",
            secret=b"mediated-test-secret",
        )
        self.record = {
            "assessment_id": "gmct-receipt-001",
            "trace_id": "trace-gmct-001",
            "timestamp": "2026-07-23T23:30:00Z",
            "mediated_composition": {
                "claimed_level": "governed_composition",
                "local_admissibility": [
                    {
                        "participant_id": "model-a",
                        "decision": "allow",
                        "policy_ref": "policy:model-a:v1",
                        "evidence": ["Source transition admitted."],
                        "receipt_ref": "declared:model-a:001",
                    },
                    {
                        "participant_id": "human-h",
                        "decision": "allow",
                        "policy_ref": "policy:human-h:v1",
                        "evidence": ["Mediation scope accepted."],
                        "receipt_ref": "declared:human-h:001",
                    },
                    {
                        "participant_id": "model-b",
                        "decision": "allow",
                        "policy_ref": "policy:model-b:v1",
                        "evidence": ["Destination transition admitted."],
                        "receipt_ref": "declared:model-b:001",
                    },
                ],
            },
        }

    def build(self, record=None):
        return build_mediated_receipts(record or self.record, signer=self.signer)

    def test_builds_one_receipt_per_local_decision(self):
        receipts, head = self.build()
        self.assertEqual(3, len(receipts))
        self.assertEqual(GENESIS_HASH, receipts[0]["previous_hash"])
        self.assertEqual(receipts[0]["receipt_hash"], receipts[1]["previous_hash"])
        self.assertEqual(receipts[-1]["receipt_hash"], head)
        self.assertTrue(verify_mediated_chain(receipts, self.signer)["verified"])

    def test_receipt_hash_covers_unsigned_transition_payload(self):
        receipts, _ = self.build()
        excluded = {
            "receipt_hash",
            "signer_id",
            "key_ref",
            "signature_algorithm",
            "signature",
        }
        payload = {key: value for key, value in receipts[0].items() if key not in excluded}
        self.assertEqual(sha256_json(payload), receipts[0]["receipt_hash"])

    def test_assessment_mutation_changes_receipt_chain(self):
        first, first_head = self.build()
        changed = copy.deepcopy(self.record)
        changed["mediated_composition"]["local_admissibility"][1]["decision"] = "defer"
        second, second_head = self.build(changed)
        self.assertNotEqual(first[0]["assessment_hash"], second[0]["assessment_hash"])
        self.assertNotEqual(first_head, second_head)

    def test_pair_only_record_produces_no_receipts(self):
        receipts, head = build_mediated_receipts(
            {"assessment_id": "pair-only"}, signer=self.signer
        )
        self.assertEqual([], receipts)
        self.assertEqual(GENESIS_HASH, head)


if __name__ == "__main__":
    unittest.main()
