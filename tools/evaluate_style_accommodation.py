#!/usr/bin/env python3
"""Measure style accommodation without converting similarity into origin claims."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

WORD_RE = re.compile(r"[A-Za-z0-9']+")
FEATURES = (
    "mean_word_length",
    "mean_sentence_length",
    "type_token_ratio",
    "punctuation_density",
    "newline_density",
    "question_density",
    "colon_density",
    "dash_density",
)


def features(text: str) -> dict[str, float]:
    words = WORD_RE.findall(text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    chars = max(len(text), 1)
    token_count = max(len(words), 1)
    return {
        "mean_word_length": sum(len(word) for word in words) / token_count,
        "mean_sentence_length": len(words) / max(len(sentences), 1),
        "type_token_ratio": len({word.lower() for word in words}) / token_count,
        "punctuation_density": sum(1 for char in text if char in ",.;:!?—-") / chars,
        "newline_density": text.count("\n") / chars,
        "question_density": text.count("?") / chars,
        "colon_density": text.count(":") / chars,
        "dash_density": (text.count("-") + text.count("—")) / chars,
    }


def euclidean(a: dict[str, float], b: dict[str, float]) -> float:
    return math.sqrt(sum((a[name] - b[name]) ** 2 for name in FEATURES))


def similarity(distance: float) -> float:
    return 1.0 / (1.0 + distance)


def evaluate(record: dict[str, Any], root: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    required = (
        "experiment_id",
        "human_baseline_path",
        "model_baseline_path",
        "human_revised_path",
        "model_followup_path",
        "minimum_identity_retention",
    )
    for key in required:
        if key not in record:
            errors.append(f"missing required field: {key}")
    if errors:
        return {"status": "FAIL", "errors": errors}, errors

    try:
        human_baseline = (root / record["human_baseline_path"]).read_text(encoding="utf-8")
        model_baseline = (root / record["model_baseline_path"]).read_text(encoding="utf-8")
        human_revised = (root / record["human_revised_path"]).read_text(encoding="utf-8")
        model_followup = (root / record["model_followup_path"]).read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(str(exc))
        return {"status": "FAIL", "errors": errors}, errors

    hb = features(human_baseline)
    mb = features(model_baseline)
    hr = features(human_revised)
    mf = features(model_followup)

    initial_distance = euclidean(hb, mb)
    final_distance = euclidean(hr, mf)
    human_shift = euclidean(hb, hr)
    model_shift = euclidean(mb, mf)
    cross_convergence = similarity(final_distance) - similarity(initial_distance)
    identity_retention = similarity(human_shift)
    model_retention = similarity(model_shift)
    minimum_identity_retention = float(record["minimum_identity_retention"])

    if not 0 <= minimum_identity_retention <= 1:
        errors.append("minimum_identity_retention must be between 0 and 1")

    accommodation_asserted = cross_convergence > 0 and not errors
    identity_preserved = identity_retention >= minimum_identity_retention
    if accommodation_asserted and not identity_preserved:
        determination = "convergence_with_identity_loss"
    elif accommodation_asserted:
        determination = "bounded_accommodation_observed"
    else:
        determination = "no_accommodation_observed"

    report = {
        "experiment_id": record["experiment_id"],
        "status": "PASS" if not errors else "FAIL",
        "determination": determination,
        "metrics": {
            "initial_cross_distance": round(initial_distance, 8),
            "final_cross_distance": round(final_distance, 8),
            "cross_convergence": round(cross_convergence, 8),
            "human_shift": round(human_shift, 8),
            "model_shift": round(model_shift, 8),
            "human_identity_retention": round(identity_retention, 8),
            "model_style_retention": round(model_retention, 8),
        },
        "governance": {
            "accommodation_is_not_origin_attribution": True,
            "agreement_not_required": True,
            "identity_retention_required_for_bounded_accommodation": True,
            "maximum_claim": "observed_feature_convergence",
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
    record = json.loads(manifest_path.read_text(encoding="utf-8"))
    report, errors = evaluate(record, manifest_path.parent)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
