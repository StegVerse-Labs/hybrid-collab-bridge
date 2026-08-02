from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


initializer = load("attribution_packet_init", "tools/init_attribution_trajectory_packet.py")
verifier = load("attribution_packet_verify", "tools/verify_attribution_trajectory_packet.py")


def inputs(tmp_path: Path):
    source = tmp_path / "source.txt"
    prompt = tmp_path / "prompt.txt"
    trajectory = tmp_path / "trajectory.txt"
    source.write_text("shared source", encoding="utf-8")
    prompt.write_text("nominal prompt", encoding="utf-8")
    trajectory.write_text("originating distinctions", encoding="utf-8")
    return source, prompt, trajectory


def test_initializer_and_verifier_complete_packet(tmp_path: Path):
    source, prompt, trajectory = inputs(tmp_path)
    packet = tmp_path / "packet"
    initializer.initialize("ATTR-TEST-PACKET-001", source, prompt, trajectory, packet)
    report, errors = verifier.verify(packet)
    assert errors == []
    assert report["packet_status"] == "COMPLETE"
    assert report["result_state"] == "PENDING"
    assert set(report["verified_conditions"]) == verifier.REQUIRED_CONDITIONS


def test_initializer_refuses_duplicate_execution(tmp_path: Path):
    source, prompt, trajectory = inputs(tmp_path)
    packet = tmp_path / "packet"
    initializer.initialize("ATTR-TEST-PACKET-002", source, prompt, trajectory, packet)
    try:
        initializer.initialize("ATTR-TEST-PACKET-002", source, prompt, trajectory, packet)
    except FileExistsError:
        pass
    else:
        raise AssertionError("duplicate initialization was not rejected")


def test_verifier_rejects_mutated_input(tmp_path: Path):
    source, prompt, trajectory = inputs(tmp_path)
    packet = tmp_path / "packet"
    initializer.initialize("ATTR-TEST-PACKET-003", source, prompt, trajectory, packet)
    copied_source = next((packet / "inputs").glob("source.*"))
    copied_source.write_text("mutated source", encoding="utf-8")
    report, errors = verifier.verify(packet)
    assert report["packet_status"] == "FAILED"
    assert any("input hash mismatch: source" in error for error in errors)


def test_verifier_rejects_identity_collision(tmp_path: Path):
    source, prompt, trajectory = inputs(tmp_path)
    packet = tmp_path / "packet"
    initializer.initialize("ATTR-TEST-PACKET-004", source, prompt, trajectory, packet)
    manifest_path = packet / "packet-manifest.json"
    import json
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["conditions"][1]["participant_slots"][0] = manifest["conditions"][0]["participant_slots"][0]
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256")
    manifest["manifest_sha256"] = initializer.canonical_hash(unsigned)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report, errors = verifier.verify(packet)
    assert report["packet_status"] == "FAILED"
    assert any("participant slot collision" in error for error in errors)
