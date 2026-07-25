import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_smallest_interoperable_handoff",
    ROOT / "tools" / "validate_smallest_interoperable_handoff.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def load(name: str):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def test_valid_minimal_handoff_is_allowed():
    assert MODULE.validate(load("smallest_interoperable_handoff.valid.json")) == []


def test_overreach_is_rejected():
    errors = MODULE.validate(load("smallest_interoperable_handoff.invalid-overreach.json"))
    assert errors
    assert any("boundary overreach" in error for error in errors)


def test_under_specification_is_rejected():
    errors = MODULE.validate(
        load("smallest_interoperable_handoff.invalid-underspecified.json")
    )
    assert errors
    assert any("evidence_references" in error for error in errors)
    assert any("unresolved downstream dependency" in error for error in errors)
