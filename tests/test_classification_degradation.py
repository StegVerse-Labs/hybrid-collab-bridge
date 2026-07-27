from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "evaluate_classification_degradation.py"
spec = importlib.util.spec_from_file_location("classification_degradation", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def classifier_report(sample_id: str, prediction: str, margin: float, known: str = "family-a") -> dict:
    return {
        "status": "PASS",
        "predictions": [
            {
                "sample_id": sample_id,
                "prediction": prediction,
                "confidence_margin": margin,
                "claim_level": "probabilistic" if prediction != "abstain" else "none",
                "known_model_family": known,
            }
        ],
    }


def accommodation(determination: str = "bounded_accommodation_observed") -> dict:
    return {
        "status": "PASS",
        "experiment_id": "ACC-001",
        "determination": determination,
        "metrics": {"cross_convergence": 0.22},
    }


def manifest() -> dict:
    return {
        "evaluation_id": "DEG-001",
        "accommodation_experiment_id": "ACC-001",
        "sample_pairs": [
            {
                "pair_id": "PAIR-001",
                "baseline_sample_id": "before-1",
                "post_interaction_sample_id": "after-1",
                "known_model_family": "family-a",
            }
        ],
    }


def test_detects_reliability_degradation_after_accommodation():
    before = classifier_report("before-1", "family-a", 0.7)
    after = classifier_report("after-1", "family-b", 0.3)
    report, errors = module.evaluate(before, after, accommodation(), manifest())
    assert errors == []
    assert report["status"] == "PASS"
    assert report["determination"] == "classification_reliability_degraded_after_accommodation"
    assert report["pair_results"][0]["reliability_change"] == "degraded"
    assert report["governance"]["correlation_is_not_causation"] is True


def test_detects_confidence_degradation_without_label_change():
    before = classifier_report("before-1", "family-a", 0.8)
    after = classifier_report("after-1", "family-a", 0.2)
    report, errors = module.evaluate(before, after, accommodation(), manifest())
    assert errors == []
    assert report["pair_results"][0]["reliability_change"] == "confidence_degraded"
    assert report["summary"]["degradation_rate"] == 1.0


def test_rejects_known_family_binding_mismatch():
    before = classifier_report("before-1", "family-a", 0.8, known="family-a")
    after = classifier_report("after-1", "family-b", 0.8, known="family-b")
    report, errors = module.evaluate(before, after, accommodation(), manifest())
    assert report["status"] == "FAIL"
    assert any("known model-family binding mismatch" in error for error in errors)


def test_rejects_accommodation_experiment_mismatch():
    acc = accommodation()
    acc["experiment_id"] = "ACC-WRONG"
    report, errors = module.evaluate(
        classifier_report("before-1", "family-a", 0.8),
        classifier_report("after-1", "family-a", 0.7),
        acc,
        manifest(),
    )
    assert report["status"] == "FAIL"
    assert any("experiment_id does not match" in error for error in errors)
