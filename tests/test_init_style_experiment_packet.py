from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "init_style_experiment_packet.py"
spec = importlib.util.spec_from_file_location("init_style_experiment_packet", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_build_packet_preserves_claim_boundary_and_execution_sufficiency():
    packet = module.build_packet(
        "HIL-REAL-001",
        "human-001",
        [("provider-a", "family-a", "v1"), ("provider-b", "family-b", "v2")],
    )
    assert packet["claim_boundary"]["maximum_claim"] == module.MAXIMUM_CLAIM
    assert packet["claim_boundary"]["origin_attribution_prohibited"] is True
    assert packet["claim_boundary"]["causation_claim_prohibited"] is True
    assert packet["publication_posture"] == "private"

    counts = Counter((sample["model_family"], sample["phase"]) for sample in packet["samples"])
    assert counts[("family-a", "baseline")] == module.BASELINE_SAMPLES_PER_FAMILY
    assert counts[("family-b", "baseline")] == module.BASELINE_SAMPLES_PER_FAMILY
    assert counts[("family-a", "followup")] == module.FOLLOWUP_SAMPLES_PER_FAMILY
    assert counts[("family-b", "followup")] == module.FOLLOWUP_SAMPLES_PER_FAMILY
    assert len({sample["sample_id"] for sample in packet["samples"]}) == len(packet["samples"])


def test_parse_model_requires_provider_family_version():
    assert module.parse_model("provider:family:v1") == ("provider", "family", "v1")


def test_packet_is_schema_compatible_before_artifact_presence_checks():
    packet = module.build_packet(
        "HIL-REAL-002",
        "human-002",
        [("provider-a", "family-a", "v1"), ("provider-b", "family-b", "v1")],
    )
    schema = json.loads((ROOT / "schemas" / "style_experiment_intake.schema.json").read_text())
    import jsonschema
    jsonschema.validate(packet, schema)
