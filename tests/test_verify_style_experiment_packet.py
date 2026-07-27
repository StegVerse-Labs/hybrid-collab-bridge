from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "verify_style_experiment_packet.py"
spec = importlib.util.spec_from_file_location("verify_style_packet", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

KEY = "packet-test-key"


def make_receipt(sample_id: str, family: str, text: str, revised: bool = False) -> dict:
    record = {
        "receipt_id": f"receipt-{sample_id}",
        "sample_id": sample_id,
        "provider": "controlled-test-provider",
        "model_family": family,
        "model_version": "v1",
        "prompt_hash": hashlib.sha256(b"controlled prompt").hexdigest(),
        "output_hash": hashlib.sha256(text.encode()).hexdigest(),
        "generated_at": "2026-07-27T00:00:00Z",
        "platform_context": "unit-test",
        "human_revision": {
            "applied": revised,
            "revision_hash": hashlib.sha256(text.encode()).hexdigest() if revised else None,
        },
        "provenance_level": "cryptographically_bound",
        "signature": {
            "algorithm": "hmac-sha256",
            "signer_id": "test-signer",
            "key_ref": "test:ephemeral",
            "value": "",
        },
    }
    record["signature"]["value"] = hmac.new(
        KEY.encode(), module.canonical_payload(record), hashlib.sha256
    ).hexdigest()
    return record


def build_packet(root: Path) -> Path:
    samples = []
    for family in ("family-a", "family-b"):
        for phase in ("baseline", "followup"):
            sample_id = f"{family}-{phase}"
            text = f"Controlled {family} {phase} output."
            text_path = root / "samples" / f"{sample_id}.txt"
            receipt_path = root / "receipts" / f"{sample_id}.json"
            text_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_text(text, encoding="utf-8")
            receipt_path.write_text(json.dumps(make_receipt(sample_id, family, text)), encoding="utf-8")
            samples.append({
                "sample_id": sample_id,
                "phase": phase,
                "text_path": str(text_path.relative_to(root)),
                "receipt_path": str(receipt_path.relative_to(root)),
                "model_family": family,
                "human_revision_applied": False,
            })
    packet = {
        "experiment_id": "HIL-VERIFY-001",
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
    packet_path = root / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    return packet_path


def test_complete_verified_packet_is_execution_ready(tmp_path: Path):
    report = module.verify(build_packet(tmp_path), KEY)
    assert report["status"] == "READY"
    assert report["execution_admissible"] is True
    assert report["publication_admissible"] is False
    assert all(sample["verified"] for sample in report["verified_samples"])


def test_mutated_sample_blocks_execution(tmp_path: Path):
    packet_path = build_packet(tmp_path)
    (tmp_path / "samples" / "family-a-baseline.txt").write_text("Mutated output.", encoding="utf-8")
    report = module.verify(packet_path, KEY)
    assert report["status"] == "BLOCKED"
    assert report["execution_admissible"] is False
    assert any("output_hash does not match" in error for error in report["errors"])


def test_family_mismatch_blocks_execution(tmp_path: Path):
    packet_path = build_packet(tmp_path)
    receipt_path = tmp_path / "receipts" / "family-b-followup.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["model_family"] = "family-a"
    receipt["signature"]["value"] = hmac.new(
        KEY.encode(), module.canonical_payload(receipt), hashlib.sha256
    ).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    report = module.verify(packet_path, KEY)
    assert report["status"] == "BLOCKED"
    assert any("model_family does not match" in error for error in report["errors"])


def test_bad_signature_blocks_execution(tmp_path: Path):
    packet_path = build_packet(tmp_path)
    receipt_path = tmp_path / "receipts" / "family-a-followup.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["signature"]["value"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    report = module.verify(packet_path, KEY)
    assert report["status"] == "BLOCKED"
    assert any("signature verification failed" in error for error in report["errors"])
