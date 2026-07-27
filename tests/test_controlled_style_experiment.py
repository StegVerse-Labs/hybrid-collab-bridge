from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "run_controlled_style_experiment.py"
spec = importlib.util.spec_from_file_location("controlled_style_experiment", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

KEY = "test-style-receipt-key"


def receipt(text: str, family: str, sample_id: str) -> dict:
    record = {
        "receipt_id": f"receipt-{sample_id}",
        "sample_id": sample_id,
        "provider": "controlled-test-provider",
        "model_family": family,
        "model_version": "test-v1",
        "prompt_hash": hashlib.sha256(b"controlled prompt").hexdigest(),
        "output_hash": hashlib.sha256(text.encode()).hexdigest(),
        "generated_at": "2026-07-27T00:00:00Z",
        "platform_context": "unit-test",
        "human_revision": {"applied": False, "revision_hash": None},
        "provenance_level": "cryptographically_bound",
        "signature": {
            "algorithm": "hmac-sha256",
            "signer_id": "test-runner",
            "key_ref": "test:ephemeral",
            "value": "",
        },
    }
    record["signature"]["value"] = hmac.new(
        KEY.encode(), module.canonical_payload(record), hashlib.sha256
    ).hexdigest()
    return record


def write_sample(root: Path, sample_id: str, family: str, text: str) -> dict:
    text_path = root / f"{sample_id}.txt"
    receipt_path = root / f"{sample_id}.receipt.json"
    text_path.write_text(text, encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt(text, family, sample_id)), encoding="utf-8")
    return {
        "sample_id": sample_id,
        "model_family": family,
        "text_path": text_path.name,
        "receipt_path": receipt_path.name,
    }


def test_runner_accepts_verified_training_and_emits_bounded_predictions(tmp_path: Path):
    training = [
        write_sample(tmp_path, "a1", "family-a", "Compact sentences. Direct claims. Few qualifiers."),
        write_sample(tmp_path, "a2", "family-a", "Brief answer. Clear statement. Minimal framing."),
        write_sample(tmp_path, "b1", "family-b", "Consider the following: a longer, exploratory explanation—one that asks questions and develops context?"),
        write_sample(tmp_path, "b2", "family-b", "There are several interacting possibilities: context, interpretation, and uncertainty. Which explanation survives review?"),
    ]
    evaluation_text = "Direct answer. Minimal framing. Clear claim."
    evaluation_path = tmp_path / "eval.txt"
    evaluation_path.write_text(evaluation_text, encoding="utf-8")
    manifest = {
        "experiment_id": "TEST-EXP-001",
        "minimum_training_samples_per_family": 2,
        "abstention_threshold": 0.05,
        "training_samples": training,
        "evaluation_samples": [
            {"sample_id": "eval-1", "text_path": evaluation_path.name, "known_model_family": "family-a"}
        ],
    }
    report, errors = module.run(manifest, tmp_path, KEY)
    assert errors == []
    assert report["status"] == "PASS"
    assert report["governance"]["maximum_claim_level"] == "probabilistic"
    assert report["predictions"][0]["prediction"] in {"family-a", "abstain"}
    assert report["predictions"][0]["claim_level"] in {"probabilistic", "none"}


def test_runner_rejects_tampered_training_output(tmp_path: Path):
    sample = write_sample(tmp_path, "a1", "family-a", "Original output.")
    (tmp_path / sample["text_path"]).write_text("Tampered output.", encoding="utf-8")
    manifest = {
        "experiment_id": "TEST-EXP-TAMPER",
        "minimum_training_samples_per_family": 1,
        "training_samples": [sample],
        "evaluation_samples": [],
    }
    report, errors = module.run(manifest, tmp_path, KEY)
    assert report["status"] == "FAIL"
    assert any("output hash does not match" in error for error in errors)


def test_runner_requires_two_verified_families(tmp_path: Path):
    sample = write_sample(tmp_path, "a1", "family-a", "Only one family exists.")
    manifest = {
        "experiment_id": "TEST-EXP-ONE-FAMILY",
        "minimum_training_samples_per_family": 1,
        "training_samples": [sample],
        "evaluation_samples": [],
    }
    _, errors = module.run(manifest, tmp_path, KEY)
    assert any("at least two model families" in error for error in errors)
