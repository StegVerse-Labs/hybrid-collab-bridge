from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = load("bundle_builder", "tools/build_style_experiment_evidence_bundle.py")
verifier = load("bundle_verifier", "tools/verify_style_experiment_evidence_bundle.py")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def experiment_root(tmp_path: Path) -> Path:
    root = tmp_path / "HIL-REAL-VERIFY-001"
    root.mkdir()
    experiment_id = "HIL-REAL-VERIFY-001"
    write_json(root / "packet.json", {"experiment_id": experiment_id})
    write_json(root / "readiness-report.json", {"experiment_id": experiment_id, "status": "READY"})
    write_json(root / "execution-plan.json", {"experiment_id": experiment_id, "status": "READY"})
    return root


def build(root: Path) -> dict:
    manifest, errors = builder.build_manifest(root)
    assert not errors
    write_json(root / "manifest.json", manifest)
    return manifest


def test_valid_bundle_is_independently_verified(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    report, errors = verifier.verify_bundle(root, manifest)
    assert errors == []
    assert report["status"] == "VERIFIED"
    assert report["integrity_verified"] is True
    assert report["reconstructability_verified"] is True
    assert report["publication_admissible"] is False
    assert report["verified_artifact_count"] == 3


def test_mutated_artifact_is_rejected(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    write_json(root / "readiness-report.json", {"experiment_id": "HIL-REAL-VERIFY-001", "status": "BLOCKED"})
    report, errors = verifier.verify_bundle(root, manifest)
    assert report["status"] == "INVALID"
    assert any("artifact hash mismatch: readiness-report.json" in error for error in errors)


def test_inventory_mutation_is_rejected(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    manifest["artifacts"][0]["size_bytes"] += 1
    _, errors = verifier.verify_bundle(root, manifest)
    assert any("artifact size mismatch" in error for error in errors)
    assert "inventory hash mismatch" in errors


def test_publication_authority_cannot_be_inserted(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    manifest["publication_admissible"] = True
    report, errors = verifier.verify_bundle(root, manifest)
    assert report["publication_admissible"] is False
    assert "evidence integrity cannot grant publication authority" in errors


def test_changed_claim_boundary_is_rejected(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    manifest["claim_boundary"]["maximum_claim"] = "verified model origin"
    _, errors = verifier.verify_bundle(root, manifest)
    assert "maximum claim boundary was changed" in errors


def test_duplicate_inventory_path_is_rejected(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    manifest["artifacts"].append(dict(manifest["artifacts"][0]))
    manifest["inventory_sha256"] = verifier.sha256_bytes(
        verifier.canonical_json(sorted(manifest["artifacts"], key=lambda row: row["path"]))
    )
    _, errors = verifier.verify_bundle(root, manifest)
    assert any("duplicate artifact inventory path" in error for error in errors)


def test_cross_artifact_experiment_id_mismatch_is_rejected(tmp_path: Path):
    root = experiment_root(tmp_path)
    manifest = build(root)
    write_json(root / "execution-plan.json", {"experiment_id": "OTHER", "status": "READY"})
    data = (root / "execution-plan.json").read_bytes()
    for row in manifest["artifacts"]:
        if row["path"] == "execution-plan.json":
            row["sha256"] = verifier.sha256_bytes(data)
            row["size_bytes"] = len(data)
    manifest["inventory_sha256"] = verifier.sha256_bytes(
        verifier.canonical_json(sorted(manifest["artifacts"], key=lambda row: row["path"]))
    )
    _, errors = verifier.verify_bundle(root, manifest)
    assert "experiment_id mismatch in execution-plan.json" in errors
