#!/usr/bin/env python3
"""Create a governed, non-evidentiary intake skeleton for a real style experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MAXIMUM_CLAIM = "observed association between interaction and classifier reliability"
BASELINE_SAMPLES_PER_FAMILY = 2
FOLLOWUP_SAMPLES_PER_FAMILY = 1


def build_packet(experiment_id: str, human_id: str, models: list[tuple[str, str, str]]) -> dict:
    samples = []
    for provider, family, version in models:
        for index in range(1, BASELINE_SAMPLES_PER_FAMILY + 1):
            sample_id = f"{family}-baseline-{index:03d}"
            samples.append({
                "sample_id": sample_id,
                "phase": "baseline",
                "text_path": f"samples/{sample_id}.txt",
                "receipt_path": f"receipts/{sample_id}.json",
                "model_family": family,
                "human_revision_applied": False,
            })
        for index in range(1, FOLLOWUP_SAMPLES_PER_FAMILY + 1):
            sample_id = f"{family}-followup-{index:03d}"
            samples.append({
                "sample_id": sample_id,
                "phase": "followup",
                "text_path": f"samples/{sample_id}.txt",
                "receipt_path": f"receipts/{sample_id}.json",
                "model_family": family,
                "human_revision_applied": False,
            })
    return {
        "experiment_id": experiment_id,
        "protocol_version": "hil-style-1.0",
        "research_question": "Does interaction alter style-classification reliability while participant identity remains meaningfully retained?",
        "participants": {
            "human_participant_id": human_id,
            "model_systems": [
                {"provider": provider, "model_family": family, "model_version": version}
                for provider, family, version in models
            ],
        },
        "samples": samples,
        "claim_boundary": {
            "maximum_claim": MAXIMUM_CLAIM,
            "origin_attribution_prohibited": True,
            "causation_claim_prohibited": True,
        },
        "publication_posture": "private",
    }


def parse_model(raw: str) -> tuple[str, str, str]:
    parts = raw.split(":", 2)
    if len(parts) != 3 or not all(parts):
        raise argparse.ArgumentTypeError("model must be PROVIDER:FAMILY:VERSION")
    return parts[0], parts[1], parts[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--human-id", required=True)
    parser.add_argument("--model", action="append", required=True, type=parse_model)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    families = {family for _, family, _ in args.model}
    if len(families) < 2:
        parser.error("at least two distinct model families are required")

    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    (root / "samples").mkdir()
    (root / "receipts").mkdir()
    packet = build_packet(args.experiment_id, args.human_id, args.model)
    (root / "packet.json").write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "README.md").write_text(
        "# Governed Style Experiment Packet\n\n"
        "This directory is an intake skeleton, not experimental evidence.\n\n"
        f"Each model family requires {BASELINE_SAMPLES_PER_FAMILY} independent baseline outputs and "
        f"{FOLLOWUP_SAMPLES_PER_FAMILY} follow-up output before execution planning can pass.\n\n"
        "Replace each empty sample file with the exact captured output, then create a matching "
        "cryptographically bound generation receipt. Do not change the claim boundary. Run "
        "`python tools/validate_style_experiment_intake.py packet.json` before evaluation or publication.\n",
        encoding="utf-8",
    )
    for sample in packet["samples"]:
        (root / sample["text_path"]).touch()
    print(root / "packet.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())