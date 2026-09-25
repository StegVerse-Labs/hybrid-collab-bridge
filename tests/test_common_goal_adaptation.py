"""Seven frozen synthetic acceptance tests on the EXISTING pair evaluator."""
import copy
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator

from tools.evaluate_common_goal_adaptation import evaluate_common_goal_adaptation, TEST_NAMES
from tools.validate_human_llm_pair_assessments import validate_record, recommended_outcome

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/human_llm_pair_assessment.schema.json").read_text())
BASE = json.loads((ROOT / "examples/human_llm_pair_assessments.jsonl").read_text().splitlines()[0])


def participant(name, *, revoked=False):
    return dict(
        participant_id=name, goal_source="declared", goals=["shared-work"],
        capacity_before=.9, capacity_after=.6 if name == "human" else .9,
        handoff_after=.9, success_before=.6, success_after=.9,
        heldout_success=.85, fixed_control_success=.65, no_feedback_success=.6,
        clarifications_before=2, clarifications_after=2, consent=True,
        revoked=revoked, attempted_after_revocation=False,
        revocation_disposition="DENY" if revoked else "NOT_APPLICABLE",
        viability_ok=True,
    )


def case():
    return dict(
        mode="synthetic", participants=[participant("human", revoked=True), participant("facilitator")],
        selected_goal="shared-work", minimum_handoff=.75, minimum_gain=.1,
        minimum_heldout=.8, maximum_clarification_increase=0,
        goal_recomputed_after_revocation=True,
        selected_goal_after_revocation=None,
        vocabulary_collision_injected=True, vocabulary_collision_detected=True,
        false_shared_goal_injected=True, false_shared_goal_flagged=True,
        local_receipts=[
            dict(participant_id="human", receipt_ref="synthetic:human", predecessor_hash="synthetic:genesis"),
            dict(participant_id="facilitator", receipt_ref="synthetic:facilitator", predecessor_hash="synthetic:human"),
        ], fixture_replay_pass=True,
    )


def wrap(data):
    record = copy.deepcopy(BASE)
    evaluated = evaluate_common_goal_adaptation(data)
    data["expected_disposition"] = evaluated["disposition"]
    data["expected_tests"] = evaluated["tests"]
    record["common_goal_adaptation"] = data
    record["overall_outcome"] = recommended_outcome(record)
    return record


class CommonGoalAdaptationTests(unittest.TestCase):
    def test_positive_all_seven_and_schema(self):
        r = wrap(case())
        self.assertEqual("PASS", r["common_goal_adaptation"]["expected_disposition"])
        self.assertEqual(set(TEST_NAMES), set(r["common_goal_adaptation"]["expected_tests"]))
        self.assertTrue(all(v == "PASS" for v in r["common_goal_adaptation"]["expected_tests"].values()))
        self.assertEqual([], list(Draft202012Validator(SCHEMA).iter_errors(r)))
        self.assertEqual([], validate_record(r))

    def test_compatible_partial_and_conflicting_goals(self):
        d = case()
        d["participants"][1]["goals"] = ["shared-work", "other-work"]
        self.assertEqual("PASS", evaluate_common_goal_adaptation(d)["tests"]["common_goal_compatibility"])
        d["participants"][1]["goals"] = ["other-work"]
        d["selected_goal"] = None
        self.assertEqual("PASS", evaluate_common_goal_adaptation(d)["tests"]["common_goal_compatibility"])
        d["selected_goal"] = "shared-work"
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["common_goal_compatibility"])
        d["participants"][0]["goal_source"] = "unexpressed"
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["common_goal_compatibility"])

    def test_capacity_change_without_extra_clarifications(self):
        d = case()
        d["participants"][0]["clarifications_after"] = 3
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["changing_capacity"])
        d["participants"][0]["clarifications_after"] = 2
        d["participants"][0]["handoff_after"] = .4
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["changing_capacity"])

    def test_heldout_and_null_control(self):
        d = case()
        d["participants"][0]["heldout_success"] = .4
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["observed_adaptation"])
        d = case()
        for p in d["participants"]:
            p["fixed_control_success"] = .91
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["observed_adaptation"])

    def test_revocation_independent_of_other_participant(self):
        d = case()
        d["participants"][0]["attempted_after_revocation"] = True
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])
        d = case()
        d["participants"][0]["revocation_disposition"] = "NOT_APPLICABLE"
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])

    def test_post_revocation_goal_must_be_independently_recomputed(self):
        d = case()
        # Both participants declared the same initial goal, but the revoked
        # human cannot authorize it after withdrawal.
        d["selected_goal_after_revocation"] = "shared-work"
        d["goal_recomputed_after_revocation"] = True
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])
        self.assertEqual("FAIL", wrap(d)["overall_outcome"])
        d["selected_goal_after_revocation"] = None
        self.assertEqual("PASS", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])

    def test_post_revocation_remaining_eligible_participants(self):
        d = case()
        d["participants"].append(participant("observer"))
        d["local_receipts"].append(dict(participant_id="observer", receipt_ref="synthetic:observer",
                                        predecessor_hash="synthetic:facilitator"))
        d["selected_goal_after_revocation"] = "shared-work"
        self.assertEqual("PASS", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])
        d["participants"][-1]["goals"] = ["different-goal"]
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])
        d["selected_goal_after_revocation"] = None
        self.assertEqual("PASS", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])

    def test_missing_post_revocation_selected_goal_fails_closed(self):
        d = case()
        del d["selected_goal_after_revocation"]
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["independent_agency"])

    def test_no_aggregate_override_of_local_viability(self):
        d = case()
        d["participants"][0]["viability_ok"] = False
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["participant_viability"])
        self.assertEqual("FAIL", wrap(d)["overall_outcome"])

    def test_falsely_inferred_shared_goal_and_vocabulary_collision(self):
        d = case()
        d["false_shared_goal_flagged"] = False
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["provenance_integrity"])
        d = case()
        d["vocabulary_collision_detected"] = False
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["provenance_integrity"])

    def test_reconstruction_exact_participant_coverage(self):
        d = case()
        d["local_receipts"].pop()
        self.assertEqual("INDETERMINATE", evaluate_common_goal_adaptation(d)["disposition"])
        d = case()
        d["fixture_replay_pass"] = False
        self.assertEqual("FAIL", evaluate_common_goal_adaptation(d)["tests"]["reconstruction"])

    def test_unsupported_result_claim_rejected(self):
        d = case()
        r = wrap(d)
        r["common_goal_adaptation"]["expected_tests"]["participant_viability"] = "FAIL"
        self.assertTrue(any("expected tests" in x for x in validate_record(r)))
        r = wrap(case())
        r["common_goal_adaptation"]["expected_disposition"] = "FAIL"
        self.assertTrue(any("expected disposition" in x for x in validate_record(r)))

    def test_legacy_assessments_unchanged(self):
        self.assertEqual([], validate_record(BASE))


if __name__ == "__main__":
    unittest.main()
