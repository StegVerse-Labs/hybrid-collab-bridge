from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "attribution_trajectory", ROOT / "tools" / "validate_attribution_trajectory_experiment.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

CONDITIONS = (
    "same_access_no_trajectory",
    "partial_trajectory",
    "full_trajectory",
    "human_only_control",
    "shared_source_control",
)


def record(no_trajectory: float, full_trajectory: float, claimed: str) -> dict:
    observations = []
    values = {
        "same_access_no_trajectory": no_trajectory,
        "partial_trajectory": (no_trajectory + full_trajectory) / 2,
        "full_trajectory": full_trajectory,
        "human_only_control": 0.45,
        "shared_source_control": 0.40,
    }
    index = 0
    for condition in CONDITIONS:
        for replicate in range(2):
            index += 1
            score = values[condition]
            observations.append({
                "observation_id": f"obs-{index}",
                "participant_id": f"participant-{index}",
                "evaluator_id": f"evaluator-{replicate + 1}",
                "condition": condition,
                "model_id": "controlled-model-v1" if condition != "human_only_control" else "none",
                "environment_id": "test-environment",
                "scores": {field: score for field in module.SCORE_FIELDS},
                "evaluator_agreement": 0.90,
                "contamination_risk": 0.05,
            })
    return {
        "experiment_id": "ATTR-TEST-001",
        "source_packet_hash": "a" * 64,
        "prompt_hash": "b" * 64,
        "trajectory_packet_hash": "c" * 64,
        "thresholds": {
            "minimum_observations_per_condition": 2,
            "minimum_evaluator_agreement": 0.70,
            "maximum_contamination_risk": 0.20,
            "trajectory_effect_threshold": 0.20,
            "interchangeability_floor": 0.75,
        },
        "observations": observations,
        "claimed_outcome": claimed,
    }


def test_supports_trajectory_dependence_when_restoration_has_material_effect():
    outcome, summary, errors = module.derive(record(0.42, 0.86, "supports_trajectory_dependence"))
    assert errors == []
    assert outcome == "supports_trajectory_dependence"
    assert summary["trajectory_effect"] == 0.44


def test_supports_interchangeability_when_no_trajectory_reproduces_structure():
    outcome, _, errors = module.derive(record(0.81, 0.86, "supports_interchangeability"))
    assert errors == []
    assert outcome == "supports_interchangeability"


def test_rejects_claim_that_conflicts_with_derived_result():
    outcome, _, errors = module.derive(record(0.42, 0.86, "supports_interchangeability"))
    assert outcome == "supports_trajectory_dependence"
    assert any("conflicts with derived outcome" in error for error in errors)


def test_contamination_forces_indeterminate():
    candidate = record(0.42, 0.86, "indeterminate")
    candidate["observations"][0]["contamination_risk"] = 0.50
    outcome, _, errors = module.derive(candidate)
    assert outcome == "indeterminate"
    assert any("excess contamination risk" in error for error in errors)
