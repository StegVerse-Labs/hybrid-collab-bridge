from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_style_experiment_evidence_bundle.py"
spec = importlib.util.spec_from_file_location("build_style_experiment_evidence_bundle", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def write_required(root: Path, experiment_id: str = "HIL-REAL-001") -> None:
    (root / "packet.json").write_text(json.dumps({"experiment_id": experiment_id}), encoding="utf-8")
    (root / "readiness-report.json").write_text(json.dumps({"status": "READY"}), encoding="utf-8")
    (root / "execution-plan.json").write_text(json.dumps({"status": "READY"}), encoding="utf-8")


def test_complete_bundle_is_hash_bound_and_not_publication_authority(tmp_path: Path):
    write_required(tmp_path)
    (tmp_path / "baseline-report.json").write_text('{"status":"PASS"}', encoding="utf-8")

    manifest, errors = module.build_manifest(tmp_path)

    assert errors == []
    assert manifest["status"] == "COMPLETE"
    assert manifest["verification_admissible"] is True
    assert manifest["publication_admissible"] is False
    assert manifest["experiment_id"] == "HIL-REAL-001"
    assert len(manifest["inventory_sha256"]) == 64
    assert [row["path"] for row in manifest["artifacts"]] == sorted(
        row["path"] for row in manifest["artifacts"]
    )
    assert manifest["claim_boundary"]["origin_attribution_prohibited"] is True


def test_missing_required_artifact_blocks_bundle(tmp_path: Path):
    (tmp_path / "packet.json").write_text('{"experiment_id":"HIL-REAL-002"}', encoding="utf-8")
    (tmp_path / "readiness-report.json").write_text('{"status":"READY"}', encoding="utf-8")

    manifest, errors = module.build_manifest(tmp_path)

    assert manifest["status"] == "BLOCKED"
    assert manifest["verification_admissible"] is False
    assert any("execution-plan.json" in error for error in errors)


def test_mutation_changes_artifact_and_inventory_hashes(tmp_path: Path):
    write_required(tmp_path)
    first, _ = module.build_manifest(tmp_path)
    first_packet = next(row for row in first["artifacts"] if row["path"] == "packet.json")

    (tmp_path / "packet.json").write_text('{"experiment_id":"HIL-REAL-001","revision":2}', encoding="utf-8")
    second, _ = module.build_manifest(tmp_path)
    second_packet = next(row for row in second["artifacts"] if row["path"] == "packet.json")

    assert first_packet["sha256"] != second_packet["sha256"]
    assert first["inventory_sha256"] != second["inventory_sha256"]


def test_output_path_cannot_escape_experiment_root(tmp_path: Path):
    try:
        module.safe_output(tmp_path, "../manifest.json")
    except SystemExit as exc:
        assert "escapes experiment root" in str(exc)
    else:
        raise AssertionError("escaping output path was accepted")
