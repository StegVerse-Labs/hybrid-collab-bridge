"""Tests for runtime schema enforcement and mediated receipt persistence."""
from __future__ import annotations

import json
from pathlib import Path

from api.app.governance.human_llm_evidence import (
    GENESIS_HASH,
    build_mediated_receipts,
    persist_mediated_receipts,
    validate_schema,
)


def pair_record() -> dict:
    names = {
        "meaning_preservation",
        "vocabulary_alignment",
        "boundary_control",
        "contradiction_detection",
        "evidence_classification",
        "audit_gap_control",
        "review_comprehension",
        "revision_integrity",
        "independent_reconstruction",
    }
    return {
        "assessment_id": "assessment-evidence-001",
        "trace_id": "trace-evidence-001",
        "timestamp": "2026-07-24T12:00:00Z",
        "claim_consequence": "low",
        "tests": {
            name: {"status": "PASS", "score": 1.0, "critical": False, "evidence": [name]}
            for name in names
        },
        "review": {
            "human_present": True,
            "comprehension_demonstrated": True,
            "objections_considered": True,
        },
        "overall_outcome": "PASS",
        "error_attribution": [],
    }


def mediated_record() -> dict:
    record = pair_record()
    record["mediated_composition"] = {
        "claimed_level": "governed_composition",
        "participants": [
            {"participant_id": "model-a", "participant_type": "model", "role": "source"},
            {"participant_id": "human-h", "participant_type": "human", "role": "intermediary"},
            {"participant_id": "model-b", "participant_type": "model", "role": "destination"},
        ],
        "continuity": [
            {"participant_id": value, "status": "verified", "evidence": ["continuity"]}
            for value in ("model-a", "human-h", "model-b")
        ],
        "channel": {"medium_state": "developing", "observations": ["relay observed"], "stateful_intermediary": True},
        "intentionality": {"model-a": "unknown", "human-h": "deliberate", "model-b": "unknown"},
        "directional_rates": [
            {"from": "model-a", "to": "human-h", "unit": "messages_per_minute", "observed": 1, "limit": 5},
            {"from": "human-h", "to": "model-b", "unit": "messages_per_minute", "observed": 1, "limit": 5},
        ],
        "permitted_scopes": [
            {"participant_id": value, "observe": ["text"], "express": ["text"], "interpret": ["text"], "execute": []}
            for value in ("model-a", "human-h", "model-b")
        ],
        "fidelity": {"symbolic": 0.9, "semantic": 0.9, "pragmatic": 0.9, "causal": 0.9, "governance": 0.9, "evidence": ["reconstruction"]},
        "local_admissibility": [
            {"participant_id": value, "decision": "allow", "policy_ref": f"policy:{value}", "evidence": ["admitted"], "receipt_ref": f"receipt:{value}"}
            for value in ("model-a", "human-h", "model-b")
        ],
        "null_models": [{"name": "generic_language", "tested": True, "result": "rejected", "evidence": ["control"]}],
        "adaptation_evidence": ["adaptation"],
        "controls": {
            "paraphrase": True,
            "intermediary_substitution": True,
            "relay_delay": True,
            "hidden_provenance": True,
            "adversarial_relay": True,
            "independent_convergence": True,
        },
        "collective_agency_claim": False,
    }
    return record


def test_pair_record_passes_schema():
    assert validate_schema(pair_record()) == []


def test_schema_rejects_undeclared_fields():
    record = pair_record()
    record["unsupported_assertion"] = True
    assert any("Additional properties" in error for error in validate_schema(record))


def test_mediated_receipts_are_ordered_and_persisted(tmp_path: Path):
    record = mediated_record()
    assert validate_schema(record) == []
    receipts, head = build_mediated_receipts(record)
    assert len(receipts) == 3
    assert receipts[0]["previous_hash"] == GENESIS_HASH
    assert receipts[1]["previous_hash"] == receipts[0]["receipt_hash"]
    assert head == receipts[-1]["receipt_hash"]

    reference = persist_mediated_receipts(record, tmp_path)
    assert reference is not None
    assert reference["chain_head"] == head
    lines = Path(reference["path"]).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["participant_id"] for line in lines] == ["model-a", "human-h", "model-b"]


def test_receipt_hash_changes_when_local_decision_changes():
    first = mediated_record()
    second = mediated_record()
    second["mediated_composition"]["local_admissibility"][1]["decision"] = "deny"
    first_receipts, first_head = build_mediated_receipts(first)
    second_receipts, second_head = build_mediated_receipts(second)
    assert first_receipts[0]["receipt_hash"] != second_receipts[0]["receipt_hash"]
    assert first_head != second_head
