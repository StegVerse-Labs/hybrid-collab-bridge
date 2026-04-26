import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cge_light"))

from app.governance.entity import EntityIdentity, EntityRegistry
from app.governance.cge_client import CGELightClient
from app.governance.admission import AdmissionGate, AdmissionResult

class TestEntityIdentity:
    def test_entity_creation(self):
        e = EntityIdentity(
            entity_id="test-001",
            entity_type="llm_adapter",
            org_id="Test-Org",
            owner_human="owner",
            owner_ai="Beta_Orionis",
            capability_set=["text-generate"],
        )
        assert e.entity_id == "test-001"
        assert e.owner_ai == "Beta_Orionis"
        assert e.governance_scope == "internal"

    def test_entity_registry(self):
        reg = EntityRegistry("Test-Org")
        e = EntityIdentity(
            entity_id="test-002",
            entity_type="automated_process",
            org_id="Test-Org",
            owner_human="owner",
        )
        reg.register(e)
        assert reg.get("test-002") == e
        assert reg.list_by_type("automated_process") == [e]

    def test_org_mismatch_raises(self):
        reg = EntityRegistry("Test-Org")
        e = EntityIdentity(
            entity_id="test-003",
            entity_type="llm_adapter",
            org_id="Wrong-Org",
            owner_human="owner",
        )
        with pytest.raises(ValueError):
            reg.register(e)

    def test_invariant_hash(self):
        e = EntityIdentity(
            entity_id="test-004",
            entity_type="llm_adapter",
            org_id="Test-Org",
            owner_human="owner",
        )
        h1 = e.compute_invariant_hash(["be_helpful", "be_honest"])
        h2 = e.compute_invariant_hash(["be_honest", "be_helpful"])
        assert h1 == h2  # Deterministic regardless of order
        assert len(h1) == 16


class TestAdmissionGate:
    @pytest.mark.asyncio
    async def test_admit_allowed(self, mock_env):
        cge = CGELightClient(org_id="Test-Org", mode="embedded")
        constitution = {
            "threshold_profiles": {
                "standard": {
                    "observability_min": 0.0,
                    "context_stability_min": 0.0,
                    "authority_clarity_min": 0.0,
                    "reversibility_margin_min": 0.0,
                    "risk_max": 1.0,
                }
            }
        }
        gate = AdmissionGate(cge, constitution)

        actor = EntityIdentity(
            entity_id="test-actor",
            entity_type="automated_process",
            org_id="Test-Org",
            owner_human="owner",
        )

        result = await gate.admit_proposal(
            proposal={"type": "test"},
            actor=actor,
        )
        assert result.decision == "allow"
        assert result.receipt is not None
        assert "verified" in result.receipt

    @pytest.mark.asyncio
    async def test_admit_denied(self, mock_env):
        cge = CGELightClient(org_id="Test-Org", mode="embedded")
        # Strict thresholds that will fail
        constitution = {
            "threshold_profiles": {
                "standard": {
                    "observability_min": 1.0,
                    "context_stability_min": 1.0,
                    "authority_clarity_min": 1.0,
                    "reversibility_margin_min": 1.0,
                    "risk_max": 0.0,
                }
            }
        }
        gate = AdmissionGate(cge, constitution)

        actor = EntityIdentity(
            entity_id="test-actor",
            entity_type="automated_process",
            org_id="Test-Org",
            owner_human="owner",
        )

        result = await gate.admit_proposal(
            proposal={"type": "test"},
            actor=actor,
        )
        assert result.decision == "deny"

    @pytest.mark.asyncio
    async def test_admit_deferrable(self, mock_env):
        cge = CGELightClient(org_id="Test-Org", mode="embedded")
        # Thresholds that are close but not quite met
        constitution = {
            "threshold_profiles": {
                "standard": {
                    "observability_min": 0.85,
                    "context_stability_min": 0.85,
                    "authority_clarity_min": 0.85,
                    "reversibility_margin_min": 0.85,
                    "risk_max": 0.15,
                }
            }
        }
        gate = AdmissionGate(cge, constitution)

        actor = EntityIdentity(
            entity_id="test-actor",
            entity_type="automated_process",
            org_id="Test-Org",
            owner_human="owner",
        )

        result = await gate.admit_proposal(
            proposal={"type": "test"},
            actor=actor,
        )
        # Should be defer (near threshold) or deny
        assert result.decision in ["defer", "deny"]
