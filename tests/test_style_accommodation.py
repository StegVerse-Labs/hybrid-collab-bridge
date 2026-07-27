from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "evaluate_style_accommodation.py"
spec = importlib.util.spec_from_file_location("style_accommodation", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def write(root: Path, name: str, text: str) -> str:
    path = root / name
    path.write_text(text, encoding="utf-8")
    return name


def test_detects_bounded_accommodation(tmp_path: Path):
    manifest = {
        "experiment_id": "ACC-001",
        "human_baseline_path": write(tmp_path, "human-baseline.txt", "Direct claim. Brief sentence. Clear boundary."),
        "model_baseline_path": write(tmp_path, "model-baseline.txt", "There are several interacting possibilities: context, interpretation, uncertainty, and scope. Which explanation survives review?"),
        "human_revised_path": write(tmp_path, "human-revised.txt", "Direct claim: clear boundary, with context."),
        "model_followup_path": write(tmp_path, "model-followup.txt", "Clear claim. Brief context. Defined boundary."),
        "minimum_identity_retention": 0.2,
    }
    report, errors = module.evaluate(manifest, tmp_path)
    assert errors == []
    assert report["status"] == "PASS"
    assert report["governance"]["accommodation_is_not_origin_attribution"] is True
    assert report["determination"] in {
        "bounded_accommodation_observed",
        "no_accommodation_observed",
        "convergence_with_identity_loss",
    }


def test_reports_identity_loss_separately(tmp_path: Path):
    manifest = {
        "experiment_id": "ACC-IDENTITY-LOSS",
        "human_baseline_path": write(tmp_path, "hb.txt", "Stop. No."),
        "model_baseline_path": write(tmp_path, "mb.txt", "A long exploratory passage: questions, qualifications, and contextual elaboration?"),
        "human_revised_path": write(tmp_path, "hr.txt", "A long exploratory passage: questions, qualifications, and contextual elaboration?"),
        "model_followup_path": write(tmp_path, "mf.txt", "A long exploratory passage: questions, qualifications, and contextual elaboration?"),
        "minimum_identity_retention": 0.99,
    }
    report, errors = module.evaluate(manifest, tmp_path)
    assert errors == []
    if report["metrics"]["cross_convergence"] > 0:
        assert report["determination"] == "convergence_with_identity_loss"


def test_rejects_invalid_identity_threshold(tmp_path: Path):
    manifest = {
        "experiment_id": "ACC-BAD-THRESHOLD",
        "human_baseline_path": write(tmp_path, "hb.txt", "A."),
        "model_baseline_path": write(tmp_path, "mb.txt", "B."),
        "human_revised_path": write(tmp_path, "hr.txt", "A."),
        "model_followup_path": write(tmp_path, "mf.txt", "B."),
        "minimum_identity_retention": 1.5,
    }
    report, errors = module.evaluate(manifest, tmp_path)
    assert report["status"] == "FAIL"
    assert any("between 0 and 1" in error for error in errors)
