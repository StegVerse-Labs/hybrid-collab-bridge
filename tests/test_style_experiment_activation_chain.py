from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


initializer = load("style_packet_initializer", ROOT / "tools" / "init_style_experiment_packet.py")
planner = load("style_execution_planner", ROOT / "tools" / "build_style_experiment_execution_plan.py")


def test_fresh_packet_has_execution_sufficient_inventory_after_verification():
    packet = initializer.build_packet(
        "HIL-ACTIVATION-001",
        "human-001",
        [
            ("provider-a", "family-a", "v1"),
            ("provider-b", "family-b", "v1"),
        ],
    )
    readiness = {
        "experiment_id": packet["experiment_id"],
        "status": "READY",
        "execution_admissible": True,
        "publication_admissible": False,
    }

    plan, errors = planner.build_plan(packet, readiness)

    assert errors == []
    assert plan["status"] == "READY"
    assert plan["execution_admissible"] is True
    assert plan["publication_admissible"] is False
    assert plan["sample_inventory"] == {
        "family-a": {"baseline": 2, "post_revision": 0, "followup": 1},
        "family-b": {"baseline": 2, "post_revision": 0, "followup": 1},
    }
    assert [task["task_id"] for task in plan["tasks"]] == [
        "verify_packet",
        "baseline_classification",
        "followup_classification",
        "accommodation_evaluation",
        "classification_degradation",
        "publication_review",
    ]


def test_publication_stays_blocked_without_independent_authority():
    packet = initializer.build_packet(
        "HIL-ACTIVATION-002",
        "human-002",
        [
            ("provider-a", "family-a", "v1"),
            ("provider-b", "family-b", "v1"),
        ],
    )
    packet["publication_posture"] = "public"
    readiness = {
        "experiment_id": packet["experiment_id"],
        "status": "READY",
        "execution_admissible": True,
        "publication_admissible": False,
    }

    plan, errors = planner.build_plan(packet, readiness)

    assert errors == []
    assert plan["execution_admissible"] is True
    assert plan["publication_admissible"] is False
