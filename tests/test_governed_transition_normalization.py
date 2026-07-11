from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMALIZER = ROOT / "scripts" / "normalize_governed_transition_candidate.py"
SDK_CANDIDATE = ROOT / "examples" / "sdk_transition_candidate.input.json"
SDK_ROUTE = ROOT / "examples" / "sdk_origin_hps_bridge_route.json"
LLM_CANDIDATE = ROOT / "examples" / "llm_transition_candidate.input.json"
LLM_ROUTE = ROOT / "examples" / "llm_origin_hps_bridge_route.json"


class GovernedTransitionNormalizationTests(unittest.TestCase):
    def run_normalizer(self, candidate: Path, route: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "normalized.json"
            result = subprocess.run(
                [sys.executable, str(NORMALIZER), str(candidate), str(route), str(output)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            normalized = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
        return result, normalized

    def assert_ready_candidate(self, source_path: Path, normalized: dict) -> None:
        source = json.loads(source_path.read_text(encoding="utf-8"))
        self.assertEqual(normalized["transition_id"], source["transition_id"])
        self.assertEqual(normalized["run_id"], source["run_id"])
        self.assertEqual(normalized["origin"]["event_id"], source["origin"]["event_id"])
        self.assertEqual(normalized["origin"]["origin_manifest_id"], source["origin"]["origin_manifest_id"])
        self.assertEqual(normalized["lifecycle_state"], "READY")
        self.assertEqual(
            normalized["relationships"]["target_ref"],
            "repository:StegVerse-Labs/Ecosystem-Delegation",
        )
        self.assertEqual(normalized["governance"]["admissibility_result"], "PENDING")
        self.assertEqual(normalized["governance"]["commit_time_validity"], "PENDING")
        self.assertIsNone(normalized["execution"]["action_ref"])
        self.assertIsNone(normalized["continuity"]["final_receipt_id"])
        self.assertIn("bridge-decision:ALLOW_NEXT_BOUNDARY", normalized["governance"]["evidence_refs"])

    def test_sdk_candidate_preserves_identity_and_routes_to_delegation(self) -> None:
        result, normalized = self.run_normalizer(SDK_CANDIDATE, SDK_ROUTE)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_ready_candidate(SDK_CANDIDATE, normalized)

    def test_llm_candidate_preserves_identity_and_routes_to_delegation(self) -> None:
        result, normalized = self.run_normalizer(LLM_CANDIDATE, LLM_ROUTE)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_ready_candidate(LLM_CANDIDATE, normalized)

    def test_origin_mismatch_fails_closed(self) -> None:
        candidate = json.loads(SDK_CANDIDATE.read_text(encoding="utf-8"))
        candidate["origin"]["origin_class"] = "LLM_ADAPTER_INPUT"
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate_path = Path(temp_dir) / "candidate.json"
            output = Path(temp_dir) / "normalized.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(NORMALIZER), str(candidate_path), str(SDK_ROUTE), str(output)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("do not match", result.stdout)


if __name__ == "__main__":
    unittest.main()
