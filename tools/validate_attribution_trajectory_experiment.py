from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "attribution_trajectory_experiment.schema.json").read_text())
REQUIRED = {
    "same_access_no_trajectory",
    "partial_trajectory",
    "full_trajectory",
    "human_only_control",
    "shared_source_control",
}
SCORE_FIELDS = (
    "problem_recognition_fidelity",
    "governing_distinction_fidelity",
    "dependency_reconstruction",
    "rejected_alternative_reconstruction",
    "authority_boundary_fidelity",
    "final_structure_similarity",
)


def derive(record: dict) -> tuple[str, dict, list[str]]:
    errors: list[str] = []
    schema_errors = sorted(Draft202012Validator(SCHEMA).iter_errors(record), key=lambda e: list(e.path))
    errors.extend(f"schema: {'/'.join(map(str, e.path))}: {e.message}" for e in schema_errors)
    if errors:
        return "indeterminate", {}, errors

    t = record["thresholds"]
    counts = Counter(o["condition"] for o in record["observations"])
    for condition in REQUIRED:
        if counts[condition] < t["minimum_observations_per_condition"]:
            errors.append(f"insufficient observations for {condition}")

    participants = [o["participant_id"] for o in record["observations"]]
    if len(set(participants)) != len(participants):
        errors.append("participant_id values must be unique across observations")

    evaluators_by_condition: dict[str, set[str]] = defaultdict(set)
    means: dict[str, list[float]] = defaultdict(list)
    for observation in record["observations"]:
        condition = observation["condition"]
        evaluators_by_condition[condition].add(observation["evaluator_id"])
        if observation["evaluator_agreement"] < t["minimum_evaluator_agreement"]:
            errors.append(f"low evaluator agreement: {observation['observation_id']}")
        if observation["contamination_risk"] > t["maximum_contamination_risk"]:
            errors.append(f"excess contamination risk: {observation['observation_id']}")
        means[condition].append(sum(observation["scores"][f] for f in SCORE_FIELDS) / len(SCORE_FIELDS))

    for condition in REQUIRED:
        if len(evaluators_by_condition[condition]) < 2:
            errors.append(f"fewer than two independent evaluators represented for {condition}")

    summary = {condition: round(sum(values) / len(values), 6) for condition, values in means.items() if values}
    if errors:
        return "indeterminate", summary, errors

    no_trajectory = summary["same_access_no_trajectory"]
    full_trajectory = summary["full_trajectory"]
    effect = full_trajectory - no_trajectory
    summary["trajectory_effect"] = round(effect, 6)

    if no_trajectory >= t["interchangeability_floor"] and effect < t["trajectory_effect_threshold"]:
        outcome = "supports_interchangeability"
    elif effect >= t["trajectory_effect_threshold"] and full_trajectory > no_trajectory:
        outcome = "supports_trajectory_dependence"
    else:
        outcome = "indeterminate"

    if record["claimed_outcome"] != outcome:
        errors.append(f"claimed_outcome {record['claimed_outcome']} conflicts with derived outcome {outcome}")
    return outcome, summary, errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_attribution_trajectory_experiment.py <record.json>", file=sys.stderr)
        return 2
    record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outcome, summary, errors = derive(record)
    print(json.dumps({"outcome": outcome, "summary": summary, "errors": errors}, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
