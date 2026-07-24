import json
import unittest
from pathlib import Path

from tools.validate_human_llm_pair_assessments import (
    recommended_outcome,
    supported_mediated_level,
    validate_record,
)


EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "human_llm_pair_assessments.jsonl"


def mediated_fixture(claimed_level="governed_composition"):
    participant_ids = ["model-a", "human-h", "model-b"]
    return {
        "claimed_level": claimed_level,
        "participants": [
            {"participant_id": "model-a", "participant_type": "model", "role": "source", "identity_evidence": ["model-a-receipt"]},
            {"participant_id": "human-h", "participant_type": "human", "role": "intermediary", "identity_evidence": ["human-review-receipt"]},
            {"participant_id": "model-b", "participant_type": "model", "role": "destination", "identity_evidence": ["model-b-receipt"]},
        ],
        "continuity": [
            {"participant_id": participant_id, "status": "verified", "evidence": [f"{participant_id}-continuity"]}
            for participant_id in participant_ids
        ],
        "channel": {
            "medium_state": "developing",
            "observations": ["source output was relayed, paraphrased, reconstructed, and answered"],
            "stateful_intermediary": True,
        },
        "intentionality": {"model-a": "inferred", "human-h": "deliberate", "model-b": "inferred"},
        "directional_rates": [
            {"from": "model-a", "to": "human-h", "unit": "distinctions_per_exchange", "observed": 2, "limit": 4},
            {"from": "human-h", "to": "model-b", "unit": "distinctions_per_exchange", "observed": 1, "limit": 3},
            {"from": "model-b", "to": "human-h", "unit": "distinctions_per_exchange", "observed": 2, "limit": 3},
        ],
        "permitted_scopes": [
            {"participant_id": participant_id, "observe": ["text"], "express": ["text"], "interpret": ["declared task"], "execute": []}
            for participant_id in participant_ids
        ],
        "fidelity": {
            "symbolic": 0.82,
            "semantic": 0.84,
            "pragmatic": 0.81,
            "causal": 0.78,
            "governance": 0.88,
            "evidence": ["independent reconstruction receipt", "transition correspondence record"],
        },
        "local_admissibility": [
            {
                "participant_id": participant_id,
                "decision": "allow",
                "policy_ref": "policy:mediated-composition:v1",
                "evidence": [f"{participant_id}-admissibility-evidence"],
                "receipt_ref": f"receipt:{participant_id}:allow",
            }
            for participant_id in participant_ids
        ],
        "null_models": [
            {"name": "common_training", "tested": True, "result": "not_rejected", "evidence": ["matched control run"]},
            {"name": "independent_convergence", "tested": True, "result": "rejected", "evidence": ["hidden-source control"]},
        ],
        "adaptation_evidence": ["later exchanges preserved target distinctions under changed wording"],
        "controls": {
            "paraphrase": True,
            "intermediary_substitution": True,
            "relay_delay": True,
            "hidden_provenance": True,
            "adversarial_relay": False,
            "independent_convergence": True,
        },
        "collective_agency_claim": False,
    }


class HumanLLMPairAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in EXAMPLES.read_text(encoding="utf-8").splitlines() if line.strip()]

    def base_record(self):
        return json.loads(json.dumps(self.records[0]))

    def test_examples_are_valid(self):
        for record in self.records:
            self.assertEqual([], validate_record(record), record["assessment_id"])

    def test_critical_failure_overrides_average(self):
        record = self.base_record()
        record["tests"]["vocabulary_alignment"].update(status="FAIL", score=0.69, critical=True)
        record["overall_outcome"] = "FAIL"
        self.assertEqual("FAIL", recommended_outcome(record))
        self.assertEqual([], validate_record(record))

    def test_high_consequence_requires_comprehension(self):
        record = self.base_record()
        record["review"]["comprehension_demonstrated"] = False
        record["overall_outcome"] = "FAIL"
        self.assertEqual("FAIL", recommended_outcome(record))

    def test_noncritical_partial_yields_partial(self):
        record = self.base_record()
        record["tests"]["revision_integrity"].update(status="PARTIAL", score=0.65, critical=False)
        record["overall_outcome"] = "PARTIAL"
        self.assertEqual("PARTIAL", recommended_outcome(record))
        self.assertEqual([], validate_record(record))

    def test_missing_structural_test_is_rejected(self):
        record = self.base_record()
        del record["tests"]["boundary_control"]
        errors = validate_record(record)
        self.assertTrue(any("missing tests" in error for error in errors))

    def test_governed_mediated_composition_is_admitted(self):
        record = self.base_record()
        record["mediated_composition"] = mediated_fixture()
        record["overall_outcome"] = "PASS"
        self.assertEqual("governed_composition", supported_mediated_level(record["mediated_composition"]))
        self.assertEqual([], validate_record(record))

    def test_relay_cannot_be_escalated_to_adaptive_interoperability(self):
        record = self.base_record()
        mediated = mediated_fixture("adaptive_interoperability")
        mediated["fidelity"]["semantic"] = 0.4
        mediated["adaptation_evidence"] = []
        record["mediated_composition"] = mediated
        record["overall_outcome"] = "FAIL"
        errors = validate_record(record)
        self.assertTrue(any("unsupported mediated escalation" in error for error in errors))
        self.assertEqual("relay", supported_mediated_level(mediated))

    def test_broken_continuity_blocks_governed_composition(self):
        record = self.base_record()
        mediated = mediated_fixture()
        mediated["continuity"][1]["status"] = "broken"
        record["mediated_composition"] = mediated
        record["overall_outcome"] = "FAIL"
        errors = validate_record(record)
        self.assertTrue(any("evidence supports adaptive_interoperability" in error for error in errors))

    def test_local_defer_forces_indeterminate(self):
        record = self.base_record()
        mediated = mediated_fixture("adaptive_interoperability")
        mediated["local_admissibility"][1]["decision"] = "defer"
        record["mediated_composition"] = mediated
        record["overall_outcome"] = "INDETERMINATE"
        self.assertEqual("INDETERMINATE", recommended_outcome(record))
        self.assertEqual([], validate_record(record))

    def test_collective_agency_requires_complete_evidence(self):
        record = self.base_record()
        mediated = mediated_fixture("collective_agency")
        mediated["collective_agency_claim"] = True
        mediated["joint_agency_evidence"] = {"persistent_joint_state": True}
        record["mediated_composition"] = mediated
        record["overall_outcome"] = "FAIL"
        errors = validate_record(record)
        self.assertTrue(any("collective agency requires complete" in error for error in errors))

    def test_observed_rate_may_not_exceed_limit(self):
        record = self.base_record()
        mediated = mediated_fixture()
        mediated["directional_rates"][0]["observed"] = 5
        mediated["directional_rates"][0]["limit"] = 4
        record["mediated_composition"] = mediated
        record["overall_outcome"] = "INDETERMINATE"
        errors = validate_record(record)
        self.assertTrue(any("observed rate" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
