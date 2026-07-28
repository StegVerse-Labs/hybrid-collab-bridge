#!/usr/bin/env python3
"""Compile a verified style-experiment packet into a fail-closed execution plan."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def build_plan(packet: dict[str, Any], readiness: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if readiness.get("status") != "READY" or readiness.get("execution_admissible") is not True:
        errors.append("packet readiness does not authorize execution")
    if readiness.get("experiment_id") not in (None, packet.get("experiment_id")):
        errors.append("readiness experiment_id does not match packet")

    declared = {m["model_family"] for m in packet.get("participants", {}).get("model_systems", [])}
    counts: Counter[tuple[str, str]] = Counter()
    by_phase: dict[str, list[dict[str, Any]]] = {"baseline": [], "post_revision": [], "followup": []}
    for sample in packet.get("samples", []):
        family = sample.get("model_family")
        phase = sample.get("phase")
        if family not in declared:
            errors.append(f"sample {sample.get('sample_id')} references undeclared family {family}")
            continue
        if phase not in by_phase:
            errors.append(f"sample {sample.get('sample_id')} has unsupported phase {phase}")
            continue
        counts[(family, phase)] += 1
        by_phase[phase].append(sample)

    for family in sorted(declared):
        if counts[(family, "baseline")] < 2:
            errors.append(f"model family {family} requires at least two baseline samples for controlled evaluation")
        if counts[(family, "followup")] < 1:
            errors.append(f"model family {family} requires at least one followup sample")

    tasks = [
        {
            "task_id": "verify_packet",
            "tool": "tools/verify_style_experiment_packet.py",
            "depends_on": [],
            "required_status": "READY",
        },
        {
            "task_id": "baseline_classification",
            "tool": "tools/run_controlled_style_experiment.py",
            "depends_on": ["verify_packet"],
            "inputs": {"phase": "baseline", "minimum_training_samples_per_family": 1},
        },
        {
            "task_id": "followup_classification",
            "tool": "tools/run_controlled_style_experiment.py",
            "depends_on": ["verify_packet"],
            "inputs": {"phase": "followup", "minimum_training_samples_per_family": 2},
        },
        {
            "task_id": "accommodation_evaluation",
            "tool": "tools/evaluate_style_accommodation.py",
            "depends_on": ["verify_packet"],
        },
        {
            "task_id": "classification_degradation",
            "tool": "tools/evaluate_classification_degradation.py",
            "depends_on": ["baseline_classification", "followup_classification", "accommodation_evaluation"],
        },
        {
            "task_id": "publication_review",
            "tool": None,
            "depends_on": ["classification_degradation"],
            "automatic": False,
            "required_publication_posture": "public",
        },
    ]

    plan = {
        "experiment_id": packet.get("experiment_id"),
        "status": "READY" if not errors else "BLOCKED",
        "execution_admissible": not errors,
        "publication_admissible": bool(
            not errors
            and readiness.get("publication_admissible") is True
            and packet.get("publication_posture") == "public"
        ),
        "sample_inventory": {
            family: {phase: counts[(family, phase)] for phase in by_phase}
            for family in sorted(declared)
        },
        "tasks": tasks,
        "governance": {
            "verification_precedes_execution": True,
            "publication_is_separate_from_execution": True,
            "origin_attribution_prohibited": True,
            "causation_claim_prohibited": True,
            "maximum_claim": "observed association between interaction and classifier reliability",
        },
        "errors": errors,
    }
    return plan, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet")
    parser.add_argument("readiness")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    readiness = json.loads(Path(args.readiness).read_text(encoding="utf-8"))
    plan, errors = build_plan(packet, readiness)
    Path(args.output).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
