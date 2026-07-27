from pathlib import Path

from tools.validate_style_attribution_observations import load_json, validate

ROOT = Path(__file__).resolve().parents[1]


def test_valid_observation_passes() -> None:
    record = load_json(ROOT / "examples/style_attribution_observation.valid.json")
    assert validate(record) == []


def test_verified_style_claim_without_provenance_fails() -> None:
    record = load_json(ROOT / "examples/style_attribution_observation.invalid-overreach.json")
    errors = validate(record)
    assert "verified attribution requires verified_provenance_present" in errors


def test_accommodation_requires_evidence() -> None:
    record = load_json(ROOT / "examples/style_attribution_observation.valid.json")
    record["accommodation"]["evidence_refs"] = []
    assert "asserted accommodation requires evidence_refs" in validate(record)


def test_similarity_does_not_force_model_attribution() -> None:
    record = load_json(ROOT / "examples/style_attribution_observation.valid.json")
    record["attribution_claim"]["level"] = "none"
    record["attribution_claim"]["basis"] = []
    assert validate(record) == []
