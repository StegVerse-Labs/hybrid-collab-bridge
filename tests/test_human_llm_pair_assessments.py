import json
import unittest
from pathlib import Path

from tools.validate_human_llm_pair_assessments import recommended_outcome, validate_record


EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "human_llm_pair_assessments.jsonl"


class HumanLLMPairAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in EXAMPLES.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_examples_are_valid(self):
        for record in self.records:
            self.assertEqual([], validate_record(record), record["assessment_id"])

    def test_critical_failure_overrides_average(self):
        record = json.loads(json.dumps(self.records[0]))
        record["tests"]["vocabulary_alignment"].update(status="FAIL", score=0.69, critical=True)
        record["overall_outcome"] = "FAIL"
        self.assertEqual("FAIL", recommended_outcome(record))
        self.assertEqual([], validate_record(record))

    def test_high_consequence_requires_comprehension(self):
        record = json.loads(json.dumps(self.records[0]))
        record["review"]["comprehension_demonstrated"] = False
        record["overall_outcome"] = "FAIL"
        self.assertEqual("FAIL", recommended_outcome(record))

    def test_noncritical_partial_yields_partial(self):
        record = json.loads(json.dumps(self.records[0]))
        record["tests"]["revision_integrity"].update(status="PARTIAL", score=0.65, critical=False)
        record["overall_outcome"] = "PARTIAL"
        self.assertEqual("PARTIAL", recommended_outcome(record))
        self.assertEqual([], validate_record(record))

    def test_missing_structural_test_is_rejected(self):
        record = json.loads(json.dumps(self.records[0]))
        del record["tests"]["boundary_control"]
        errors = validate_record(record)
        self.assertTrue(any("missing tests" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
