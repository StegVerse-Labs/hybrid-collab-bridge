from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools/build_style_generation_receipt.py"
VALIDATOR_PATH = ROOT / "tools/validate_style_generation_receipts.py"
SCHEMA = json.loads((ROOT / "schemas/style_generation_receipt.schema.json").read_text())

spec = importlib.util.spec_from_file_location("style_receipt_validator", VALIDATOR_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def build(tmp_path: Path, signed: bool) -> tuple[Path, dict]:
    prompt = tmp_path / "prompt.txt"
    output = tmp_path / "output.txt"
    receipt = tmp_path / "receipt.json"
    prompt.write_text("Explain individual significance.", encoding="utf-8")
    output.write_text("Significance begins when an entity assigns value.", encoding="utf-8")
    env = os.environ.copy()
    if signed:
        env.update({
            "HCB_STYLE_RECEIPT_KEY": "test-key",
            "HCB_STYLE_RECEIPT_SIGNER_ID": "test-signer",
            "HCB_STYLE_RECEIPT_KEY_REF": "test:key:1",
        })
    else:
        for name in ("HCB_STYLE_RECEIPT_KEY", "HCB_STYLE_RECEIPT_SIGNER_ID", "HCB_STYLE_RECEIPT_KEY_REF"):
            env.pop(name, None)
    subprocess.run([
        sys.executable, str(BUILDER),
        "--sample-id", "SAMPLE-001",
        "--provider", "controlled-test",
        "--model-family", "test-family",
        "--model-version", "test-version",
        "--prompt", str(prompt),
        "--output", str(output),
        "--platform-context", "local-controlled-fixture",
        "--out", str(receipt),
    ], check=True, env=env)
    return receipt, json.loads(receipt.read_text())


def test_asserted_receipt_is_bounded(tmp_path: Path, monkeypatch) -> None:
    _, record = build(tmp_path, signed=False)
    monkeypatch.delenv("HCB_STYLE_RECEIPT_KEY", raising=False)
    assert record["provenance_level"] == "asserted"
    assert module.validate(record, SCHEMA) == []


def test_signed_receipt_verifies_and_mutation_fails(tmp_path: Path, monkeypatch) -> None:
    _, record = build(tmp_path, signed=True)
    monkeypatch.setenv("HCB_STYLE_RECEIPT_KEY", "test-key")
    assert record["provenance_level"] == "cryptographically_bound"
    assert module.validate(record, SCHEMA) == []
    record["model_family"] = "mutated-family"
    assert "signature verification failed" in module.validate(record, SCHEMA)


def test_revision_state_is_consistent(tmp_path: Path, monkeypatch) -> None:
    _, record = build(tmp_path, signed=False)
    monkeypatch.delenv("HCB_STYLE_RECEIPT_KEY", raising=False)
    record["human_revision"] = {"applied": True, "revision_hash": None}
    assert "human revision requires revision_hash" in module.validate(record, SCHEMA)
