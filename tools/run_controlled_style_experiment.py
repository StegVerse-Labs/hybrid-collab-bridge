#!/usr/bin/env python3
"""Run a governed, receipt-bound baseline style-classification experiment.

The runner never treats stylistic similarity as verified origin. Training samples must
carry cryptographically bound generation receipts, and predictions are reported as
probabilistic experimental results with explicit abstention.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import re
from collections import Counter, defaultdict
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


def canonical_payload(record: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in record.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_receipt(receipt: dict[str, Any], text: str, key: str) -> list[str]:
    errors: list[str] = []
    if receipt.get("provenance_level") != "cryptographically_bound":
        errors.append("training receipt is not cryptographically_bound")
    if receipt.get("output_hash") != sha256_text(text):
        errors.append("output hash does not match sample text")
    signature = receipt.get("signature") or {}
    if signature.get("algorithm") != "hmac-sha256":
        errors.append("receipt signature algorithm is not hmac-sha256")
    else:
        expected = hmac.new(key.encode(), canonical_payload(receipt), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, str(signature.get("value", ""))):
            errors.append("receipt signature verification failed")
    return errors


def stylometric_features(text: str) -> dict[str, float]:
    words = WORD_RE.findall(text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    chars = max(len(text), 1)
    tokens = max(len(words), 1)
    return {
        "mean_word_length": sum(map(len, words)) / tokens,
        "mean_sentence_length": len(words) / max(len(sentences), 1),
        "type_token_ratio": len({w.lower() for w in words}) / tokens,
        "punctuation_density": sum(1 for c in text if c in ",.;:!?—-") / chars,
        "newline_density": text.count("\n") / chars,
        "question_density": text.count("?") / chars,
        "colon_density": text.count(":") / chars,
        "dash_density": (text.count("-") + text.count("—")) / chars,
    }


def distance(a: dict[str, float], b: dict[str, float], scales: dict[str, float]) -> float:
    return math.sqrt(sum(((a[name] - b[name]) / scales[name]) ** 2 for name in FEATURES))


def centroid(rows: list[dict[str, float]]) -> dict[str, float]:
    return {name: sum(row[name] for row in rows) / len(rows) for name in FEATURES}


def run(manifest: dict[str, Any], root: Path, key: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    training: dict[str, list[dict[str, float]]] = defaultdict(list)
    training_counts: Counter[str] = Counter()

    for sample in manifest.get("training_samples", []):
        try:
            text = (root / sample["text_path"]).read_text(encoding="utf-8")
            receipt = json.loads((root / sample["receipt_path"]).read_text(encoding="utf-8"))
        except (KeyError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"training sample load failed: {exc}")
            continue
        problems = verify_receipt(receipt, text, key)
        if receipt.get("model_family") != sample.get("model_family"):
            problems.append("manifest model_family does not match receipt")
        if problems:
            errors.extend(f"{sample.get('sample_id', 'unknown')}: {problem}" for problem in problems)
            continue
        family = sample["model_family"]
        training[family].append(stylometric_features(text))
        training_counts[family] += 1

    min_per_family = int(manifest.get("minimum_training_samples_per_family", 2))
    eligible = {family: rows for family, rows in training.items() if len(rows) >= min_per_family}
    if len(eligible) < 2:
        errors.append("at least two model families with sufficient verified training samples are required")

    all_rows = [row for rows in eligible.values() for row in rows]
    scales = {
        name: max(
            math.sqrt(sum((row[name] - sum(r[name] for r in all_rows) / len(all_rows)) ** 2 for row in all_rows) / len(all_rows)),
            1e-9,
        )
        for name in FEATURES
    } if all_rows else {name: 1.0 for name in FEATURES}
    centroids = {family: centroid(rows) for family, rows in eligible.items()}

    threshold = float(manifest.get("abstention_threshold", 0.25))
    predictions: list[dict[str, Any]] = []
    for sample in manifest.get("evaluation_samples", []):
        try:
            text = (root / sample["text_path"]).read_text(encoding="utf-8")
        except (KeyError, OSError) as exc:
            errors.append(f"evaluation sample load failed: {exc}")
            continue
        feats = stylometric_features(text)
        ranked = sorted((distance(feats, center, scales), family) for family, center in centroids.items())
        if len(ranked) < 2:
            prediction = "abstain"
            margin = 0.0
        else:
            best_distance, best_family = ranked[0]
            second_distance = ranked[1][0]
            margin = (second_distance - best_distance) / max(second_distance, 1e-9)
            prediction = best_family if margin >= threshold else "abstain"
        predictions.append({
            "sample_id": sample.get("sample_id"),
            "prediction": prediction,
            "confidence_margin": round(margin, 6),
            "claim_level": "probabilistic" if prediction != "abstain" else "none",
            "known_model_family": sample.get("known_model_family"),
            "distances": {family: round(dist, 6) for dist, family in ranked},
        })

    scored = [p for p in predictions if p["known_model_family"]]
    correct = sum(p["prediction"] == p["known_model_family"] for p in scored)
    non_abstained = sum(p["prediction"] != "abstain" for p in scored)
    report = {
        "experiment_id": manifest.get("experiment_id"),
        "governance": {
            "verified_training_receipts_required": True,
            "style_is_not_verified_origin": True,
            "maximum_claim_level": "probabilistic",
            "abstention_enabled": True,
        },
        "training_counts": dict(sorted(training_counts.items())),
        "eligible_model_families": sorted(eligible),
        "feature_names": list(FEATURES),
        "predictions": predictions,
        "metrics": {
            "scored_samples": len(scored),
            "accuracy_including_abstentions": correct / len(scored) if scored else None,
            "coverage": non_abstained / len(scored) if scored else None,
        },
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    key = os.getenv("HCB_STYLE_RECEIPT_KEY")
    if not key:
        raise SystemExit("HCB_STYLE_RECEIPT_KEY is required")
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report, errors = run(manifest, manifest_path.parent, key)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
