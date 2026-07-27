from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate_style_experiment_intake.py"
spec = importlib.util.spec_from_file_location("style_experiment_intake", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

SCHEMA = json.loads((ROOT / "schemas" / "style_experiment_intake.schema.json").read_text())


def write_files(root: Path, names: list[str]) -> None:
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("sample", encoding="utf-8")


def packet() -> dict:
    samples = []
    for family in ("family-a", "family-b"):
        for phase in ("baseline", "followup"):
            sid = f"{family}-{phase}"
            samples.append({
                "sample_id": sid,
                "phase": phase,
                "text_path": f"samples/{sid}.txt",
                "receipt_path": f"receipts/{sid}.json",
                "model_family": family,
                "human_revision_applied": False,
            })
    return {
        "experiment_id": "HIL-INTAKE-001",
        "protocol_version": "hil-style-1.0",
        "research_question": "Does interaction change classifier reliability while preserving identity?",
        "participants": {
            "human_participant_id": "human-001",
            "model_systems": [
                {"provider": "provider-a", "model_family": "family-a", "model_version": "v1"},
                {"provider": "provider-b", "model_family": "family-b", "model_version": "v1"},
            ],
        },
        "samples": samples,
        "claim_boundary": {
            "maximum_claim": "observed association between interaction and classifier reliability",
            "origin_attribution_prohibited": True,
            "causation_claim_prohibited": True,
        },
        "publication_posture": "reviewable",
    }


def materialize(root: Path, data: dict) -> None:
    names = []
    for sample in data["samples"]:
        names.extend([sample["text_path"], sample["receipt_path"]])
    write_files(root, names)


def test_valid_packet_passes(tmp_path: Path):
    data = packet()
    materialize(tmp_path, data)
    assert module.validate(data, SCHEMA, tmp_path) == []


def test_undeclared_family_fails(tmp_path: Path):
    data = packet()
    data["samples"][0]["model_family"] = "family-x"
    materialize(tmp_path, data)
    errors = module.validate(data, SCHEMA, tmp_path)
    assert any("undeclared model family" in error for error in errors)


def test_missing_followup_fails(tmp_path: Path):
    data = packet()
    data["samples"] = [s for s in data["samples"] if not (s["model_family"] == "family-b" and s["phase"] == "followup")]
    data["samples"].append({
        "sample_id": "family-b-post-revision",
        "phase": "post_revision",
        "text_path": "samples/family-b-post-revision.txt",
        "receipt_path": "receipts/family-b-post-revision.json",
        "model_family": "family-b",
        "human_revision_applied": True,
    })
    materialize(tmp_path, data)
    errors = module.validate(data, SCHEMA, tmp_path)
    assert any("requires at least one followup" in error for error in errors)


def test_path_escape_fails(tmp_path: Path):
    data = packet()
    data["samples"][0]["text_path"] = "../escaped.txt"
    materialize(tmp_path, {**data, "samples": data["samples"][1:]})
    errors = module.validate(data, SCHEMA, tmp_path)
    assert any("escapes packet root" in error for error in errors)
