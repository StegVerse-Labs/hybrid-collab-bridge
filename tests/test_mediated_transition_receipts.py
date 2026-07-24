import copy
import unittest

from tools.build_mediated_transition_receipts import GENESIS_HASH, build_receipts, sha256_json


class MediatedTransitionReceiptTests(unittest.TestCase):
    def setUp(self):
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

    def test_builds_one_receipt_per_local_decision(self):
        receipts, head = build_receipts(self.record)
        self.assertEqual(3, len(receipts))
        self.assertEqual(GENESIS_HASH, receipts[0]["previous_hash"])
        self.assertEqual(receipts[0]["receipt_hash"], receipts[1]["previous_hash"])
        self.assertEqual(receipts[-1]["receipt_hash"], head)

    def test_receipt_hash_excludes_receipt_hash_field(self):
        receipts, _ = build_receipts(self.record)
        payload = {key: value for key, value in receipts[0].items() if key != "receipt_hash"}
        self.assertEqual(sha256_json(payload), receipts[0]["receipt_hash"])

    def test_assessment_mutation_changes_receipt_chain(self):
        first, first_head = build_receipts(self.record)
        changed = copy.deepcopy(self.record)
        changed["mediated_composition"]["local_admissibility"][1]["decision"] = "defer"
        second, second_head = build_receipts(changed)
        self.assertNotEqual(first[0]["assessment_hash"], second[0]["assessment_hash"])
        self.assertNotEqual(first_head, second_head)

    def test_pair_only_record_produces_no_receipts(self):
        receipts, head = build_receipts({"assessment_id": "pair-only"})
        self.assertEqual([], receipts)
        self.assertEqual(GENESIS_HASH, head)


if __name__ == "__main__":
    unittest.main()
