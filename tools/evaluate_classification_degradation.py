#!/usr/bin/env python3
"""Link accommodation measurements to changes in classification reliability.

This evaluator compares paired baseline and post-interaction classifier results. It
never upgrades stylistic classification to verified origin and fails closed when
sample identity, known labels, or accommodation experiment bindings disagree.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def index_predictions(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for prediction in report.get("predictions", []):
        sample_id = prediction.get("sample_id")
        if not sample_id or sample_id in indexed:
            raise ValueError("predictions require unique non-empty sample_id values")
        indexed[sample_id] = prediction
    return indexed


def evaluate(
    baseline: dict[str, Any],
    post_interaction: dict[str, Any],
    accommodation: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if baseline.get("status") != "PASS":
        errors.append("baseline classifier report must have PASS status")
    if post_interaction.get("status") != "PASS":
        errors.append("post-interaction classifier report must have PASS status")
    if accommodation.get("status") != "PASS":
        errors.append("accommodation report must have PASS status")

    expected_experiment = manifest.get("accommodation_experiment_id")
    if expected_experiment and accommodation.get("experiment_id") != expected_experiment:
        errors.append("accommodation experiment_id does not match manifest")

    try:
        before = index_predictions(baseline)
        after = index_predictions(post_interaction)
    except ValueError as exc:
        errors.append(str(exc))
        before, after = {}, {}

    pairs = manifest.get("sample_pairs") or []
    if not pairs:
        errors.append("sample_pairs must contain at least one pair")

    results: list[dict[str, Any]] = []
    for pair in pairs:
        pair_id = pair.get("pair_id")
        before_id = pair.get("baseline_sample_id")
        after_id = pair.get("post_interaction_sample_id")
        if before_id not in before or after_id not in after:
            errors.append(f"{pair_id or 'unknown'}: paired prediction missing")
            continue
        b = before[before_id]
        a = after[after_id]
        known_before = b.get("known_model_family")
        known_after = a.get("known_model_family")
        expected_family = pair.get("known_model_family")
        if known_before != known_after or (expected_family and known_before != expected_family):
            errors.append(f"{pair_id}: known model-family binding mismatch")
            continue

        before_margin = float(b.get("confidence_margin", 0.0))
        after_margin = float(a.get("confidence_margin", 0.0))
        before_prediction = b.get("prediction")
        after_prediction = a.get("prediction")
        before_correct = bool(known_before and before_prediction == known_before)
        after_correct = bool(known_after and after_prediction == known_after)
        before_abstained = before_prediction == "abstain"
        after_abstained = after_prediction == "abstain"

        if before_correct and not after_correct:
            reliability_change = "degraded"
        elif not before_correct and after_correct:
            reliability_change = "improved"
        elif not before_abstained and after_abstained:
            reliability_change = "coverage_degraded"
        elif before_abstained and not after_abstained:
            reliability_change = "coverage_improved"
        elif after_margin < before_margin:
            reliability_change = "confidence_degraded"
        elif after_margin > before_margin:
            reliability_change = "confidence_improved"
        else:
            reliability_change = "unchanged"

        results.append({
            "pair_id": pair_id,
            "baseline_sample_id": before_id,
            "post_interaction_sample_id": after_id,
            "known_model_family": known_before,
            "baseline_prediction": before_prediction,
            "post_interaction_prediction": after_prediction,
            "baseline_correct": before_correct,
            "post_interaction_correct": after_correct,
            "baseline_margin": before_margin,
            "post_interaction_margin": after_margin,
            "margin_delta": round(after_margin - before_margin, 8),
            "reliability_change": reliability_change,
        })

    degraded = sum(r["reliability_change"] in {"degraded", "coverage_degraded", "confidence_degraded"} for r in results)
    improved = sum(r["reliability_change"] in {"improved", "coverage_improved", "confidence_improved"} for r in results)
    unchanged = len(results) - degraded - improved
    accommodation_determination = accommodation.get("determination")
    convergence = (accommodation.get("metrics") or {}).get("cross_convergence")

    if degraded and accommodation_determination in {
        "bounded_accommodation_observed",
        "convergence_with_identity_loss",
    }:
        overall = "classification_reliability_degraded_after_accommodation"
    elif improved and not degraded:
        overall = "classification_reliability_improved_after_interaction"
    elif results:
        overall = "mixed_or_stable_reliability"
    else:
        overall = "indeterminate"

    report = {
        "evaluation_id": manifest.get("evaluation_id"),
        "status": "PASS" if not errors else "FAIL",
        "determination": overall,
        "accommodation": {
            "experiment_id": accommodation.get("experiment_id"),
            "determination": accommodation_determination,
            "cross_convergence": convergence,
        },
        "pair_results": results,
        "summary": {
            "pair_count": len(results),
            "degraded_count": degraded,
            "improved_count": improved,
            "unchanged_count": unchanged,
            "degradation_rate": degraded / len(results) if results else None,
        },
        "governance": {
            "classification_remains_probabilistic": True,
            "accommodation_is_not_origin_attribution": True,
            "correlation_is_not_causation": True,
            "verified_origin_requires_generation_receipt": True,
            "maximum_claim": "observed_association_between_interaction_and_classifier_reliability",
        },
        "errors": errors,
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    try:
        baseline = json.loads((root / manifest["baseline_report_path"]).read_text(encoding="utf-8"))
        post_interaction = json.loads((root / manifest["post_interaction_report_path"]).read_text(encoding="utf-8"))
        accommodation = json.loads((root / manifest["accommodation_report_path"]).read_text(encoding="utf-8"))
        report, errors = evaluate(baseline, post_interaction, accommodation, manifest)
    except (KeyError, OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
        report = {"status": "FAIL", "errors": errors}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
