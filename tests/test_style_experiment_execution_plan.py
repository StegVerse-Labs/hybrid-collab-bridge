from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_style_experiment_execution_plan.py"
spec = importlib.util.spec_from_file_location("style_execution_plan", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def packet(baselines_per_family: int = 2) -> dict:
    samples = []
    for family in ("family-a", "family-b"):
        for index in range(baselines_per_family):
            samples.append({
                "sample_id": f"{family}-baseline-{index}",
                "phase": "baseline",
                "text_path": f"samples/{family}-baseline-{index}.txt",
                "receipt_path": f"receipts/{family}-baseline-{index}.json",
                "model_family": family,
            })
        samples.append({
            "sample_id": f"{family}-followup",
            "phase": "followup",
            "text_path": f"samples/{family}-followup.txt",
            "receipt_path": f"receipts/{family}-followup.json",
            "model_family": family,
        })
    return {
        "experiment_id": "HIL-PLAN-001",
        "participants": {
            "model_systems": [
                {"provider": "p1", "model_family": "family-a", "model_version": "v1"},
                {"provider": "p2", "model_family": "family-b", "model_version": "v1"},
            ]
        },
        "samples": samples,
        "publication_posture": "reviewable",
    }


def readiness(**overrides) -> dict:
    data = {
        "experiment_id": "HIL-PLAN-001",
        "status": "READY",
        "execution_admissible": True,
        "publication_admissible": False,
    }
    data.update(overrides)
    return data


def test_ready_packet_compiles_ordered_plan():
    plan, errors = module.build_plan(packet(), readiness())
    assert errors == []
    assert plan["status"] == "READY"
    assert plan["execution_admissible"] is True
    tasks = {task["task_id"]: task for task in plan["tasks"]}
    assert tasks["classification_degradation"]["depends_on"] == [
        "baseline_classification", "followup_classification", "accommodation_evaluation"
    ]
    assert plan["publication_admissible"] is False


def test_unready_packet_is_blocked():
    plan, errors = module.build_plan(packet(), readiness(status="BLOCKED", execution_admissible=False))
    assert plan["status"] == "BLOCKED"
    assert any("does not authorize execution" in error for error in errors)


def test_insufficient_baseline_samples_are_blocked():
    plan, errors = module.build_plan(packet(baselines_per_family=1), readiness())
    assert plan["execution_admissible"] is False
    assert sum("requires at least two baseline" in error for error in errors) == 2


def test_publication_requires_separate_authority():
    public_packet = packet()
    public_packet["publication_posture"] = "public"
    plan, errors = module.build_plan(public_packet, readiness(publication_admissible=True))
    assert errors == []
    assert plan["publication_admissible"] is True
    assert plan["governance"]["publication_is_separate_from_execution"] is True


def test_readiness_for_another_experiment_is_rejected():
    plan, errors = module.build_plan(packet(), readiness(experiment_id="HIL-OTHER"))
    assert plan["status"] == "BLOCKED"
    assert any("does not match packet" in error for error in errors)
