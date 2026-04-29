"""StegVerse-SDK Alignment Module.

Ensures the user-facing SDK adapter shares the same governance surface
as the internal bridge adapter. Both adapters speak the same language:
PROPOSE → ADMIT → EXECUTE → PROVE → RECEIPT

This module provides:
- Shared governance interface for SDK and bridge
- Cross-adapter receipt verification
- Unified entity identity schema
- Common admission surface
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .entity import EntityIdentity
from .cge_client import CGELightClient
from .admission import AdmissionGate, AdmissionResult


@dataclass
class GovernedOutput:
    """Unified output format for both SDK and bridge."""
    decision: str  # allow | deny | defer
    receipt: Dict[str, Any]
    bcat: Dict[str, Any]
    gcat: Dict[str, Any]
    reasoning: str
    output: Optional[str] = None
    entity_id: str = ""


class SharedGovernanceSurface:
    """Shared governance surface for SDK + Bridge parity.

    Usage (SDK side):
        surface = SharedGovernanceSurface(cge_client, constitution)
        result = surface.govern_llm_output(
            provider="openai",
            model="gpt-4",
            prompt="...",
            output=llm_output,
            entity=user_entity,
        )
        # Returns: allow | deny | defer + receipt + reasoning

    Usage (Bridge side):
        surface = SharedGovernanceSurface(cge_client, constitution)
        result = surface.govern_expert_output(
            expert="claude",
            output=expert_output,
            entity=bridge_entity,
        )
        # Same format — full parity
    """

    def __init__(self, cge_client: CGELightClient, constitution: Dict[str, Any]):
        self.gate = AdmissionGate(cge_client, constitution)
        self.cge = cge_client

    async def govern_llm_output(
        self,
        provider: str,
        model: str,
        prompt: str,
        output: str,
        entity: EntityIdentity,
    ) -> GovernedOutput:
        """Govern user-facing LLM output (SDK pattern)."""
        proposal = {
            "type": "llm_output",
            "provider": provider,
            "model": model,
            "prompt_hash": hash(prompt) & 0xFFFFFFFF,
            "output": output,
        }

        admission = await self.gate.admit_proposal(
            proposal=proposal,
            actor=entity,
            source=f"sdk/{provider}",
        )

        return GovernedOutput(
            decision=admission.decision,
            receipt=admission.receipt,
            bcat=admission.bcat,
            gcat=admission.gcat,
            reasoning=admission.reasoning,
            output=output if admission.decision == "allow" else None,
            entity_id=entity.entity_id,
        )

    async def govern_expert_output(
        self,
        expert: str,
        output: str,
        entity: EntityIdentity,
    ) -> GovernedOutput:
        """Govern internal expert output (Bridge pattern)."""
        proposal = {
            "type": "expert_output",
            "expert": expert,
            "output": output,
        }

        admission = await self.gate.admit_proposal(
            proposal=proposal,
            actor=entity,
            source=f"bridge/{expert}",
        )

        return GovernedOutput(
            decision=admission.decision,
            receipt=admission.receipt,
            bcat=admission.bcat,
            gcat=admission.gcat,
            reasoning=admission.reasoning,
            output=output if admission.decision == "allow" else None,
            entity_id=entity.entity_id,
        )

    async def verify_cross_adapter(
        self,
        sdk_receipt: Dict[str, Any],
        bridge_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify that SDK and bridge receipts are consistent.

        Used when both adapters process the same request
        (e.g., user SDK + internal bridge in parallel).
        """
        from cge_light.cge.receipts import verify_receipt
        from cge_light.cge.hashing import digest_object

        sdk_valid = verify_receipt(sdk_receipt)
        bridge_valid = verify_receipt(bridge_receipt)

        # Check that both receipts reference the same payload hash
        sdk_hash = sdk_receipt.get("payload_hash", "")
        bridge_hash = bridge_receipt.get("payload_hash", "")

        consistent = sdk_hash == bridge_hash if (sdk_hash and bridge_hash) else False

        return {
            "sdk_valid": sdk_valid,
            "bridge_valid": bridge_valid,
            "consistent": consistent,
            "sdk_decision": sdk_receipt.get("decision"),
            "bridge_decision": bridge_receipt.get("decision"),
            "quorum": sdk_valid and bridge_valid and consistent,
        }
