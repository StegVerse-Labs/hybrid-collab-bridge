from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "evaluate_style_attribution_corpus.py"
SPEC = importlib.util.spec_from_file_location("style_corpus", TOOL)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_initial_corpus_is_valid_and_bounded() -> None:
    records = MODULE.load_jsonl(ROOT / "examples" / "style_attribution_corpus.jsonl")
    assert MODULE.validate(records) == []
    report = MODULE.summarize(records)
    assert report["record_count"] == 4
    assert report["model_classification_ready"] is False
    assert report["records_with_known_model_family"] == 0


def test_verified_claim_requires_generation_receipt() -> None:
    record = {
        "sample_id": "BAD-001",
        "trace_id": "TRACE",
        "text": "sample",
        "known_conditions": {
            "model_family": "unknown",
            "prompt_pattern": "unknown",
            "platform": "generic",
            "human_revision": "unknown",
            "interactional_accommodation": "unknown",
        },
        "labels": ["cadence"],
        "provenance_level": "synthetic_control",
        "permitted_claim": "verified",
        "_line": 1,
    }
    errors = MODULE.validate([record])
    assert "line 1: verified claim lacks verified generation provenance" in errors


def test_duplicate_sample_ids_fail() -> None:
    base = {
        "sample_id": "DUP",
        "trace_id": "TRACE",
        "text": "sample",
        "known_conditions": {
            "model_family": "unknown",
            "prompt_pattern": "unknown",
            "platform": "generic",
            "human_revision": "unknown",
            "interactional_accommodation": "unknown",
        },
        "labels": ["cadence"],
        "provenance_level": "synthetic_control",
        "permitted_claim": "descriptive",
    }
    first = dict(base, _line=1)
    second = dict(base, _line=2)
    assert "line 2: duplicate sample_id DUP" in MODULE.validate([first, second])
