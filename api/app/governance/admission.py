"""Admission gate: BCAT/GCAT evaluation before execution.

Every proposal, every expert output, every consensus merge must pass
admission before execution. Human gate is exception-only.
"""
from __future__ import annotations
from typing import Dict, Any, Literal
from dataclasses import dataclass

from .entity import EntityIdentity
from .cge_client import CGELightClient


Decision = Literal["allow", "deny", "defer"]


@dataclass
class AdmissionResult:
    decision: Decision
    receipt: Dict[str, Any]
    bcat: Dict[str, Any]
    gcat: Dict[str, Any]
    reasoning: str
    requires_human: bool = False
    requires_ai_quorum: bool = False


class AdmissionGate:
    """Gatekeeper for all bridge operations."""

    def __init__(self, cge_client: CGELightClient, constitution: Dict[str, Any]):
        self.cge = cge_client
        self.constitution = constitution
        self.thresholds = constitution.get("threshold_profiles", {}).get("standard", {})

    async def admit_proposal(
        self,
        proposal: Dict[str, Any],
        actor: EntityIdentity,
        source: str = "hybrid-collab-bridge",
    ) -> AdmissionResult:
        """Admit a single proposal before execution."""
        ingest_result = await self.cge.ingest(
            payload=proposal,
            source=source,
            actor=actor,
            mutation_class="ingest",
        )

        bcat = ingest_result.get("bcat", {})
        gcat = ingest_result.get("gcat", {})
        admissible = ingest_result.get("admissible", False)

        if not admissible:
            if self._is_deferrable(bcat, gcat):
                decision: Decision = "defer"
                requires_human = True
                reasoning = "BCAT/GCAT near threshold; requires human review"
            else:
                decision = "deny"
                requires_human = False
                reasoning = "BCAT/GCAT below threshold; denied"
        else:
            decision = "allow"
            requires_human = False
            reasoning = "BCAT/GCAT admissible; auto-approved"

        receipt = await self.cge.append_ledger(
            mutation_class="approve" if decision == "allow" else "reject",
            actor=actor,
            payload=proposal,
            bcat=bcat,
            gcat=gcat,
        )

        return AdmissionResult(
            decision=decision,
            receipt=receipt,
            bcat=bcat,
            gcat=gcat,
            reasoning=reasoning,
            requires_human=requires_human,
        )

    async def admit_consensus_merge(
        self,
        proposals: list,
        merge_output: Dict[str, Any],
        referee_actor: EntityIdentity,
    ) -> AdmissionResult:
        """Admit the consensus merge result."""
        ingest_result = await self.cge.ingest(
            payload={
                "proposals_count": len(proposals),
                "merge_output": merge_output,
                "strategy": "consensus",
            },
            source="hybrid-collab-bridge/consensus",
            actor=referee_actor,
            mutation_class="derive",
        )

        bcat = ingest_result.get("bcat", {})
        gcat = ingest_result.get("gcat", {})
        admissible = ingest_result.get("admissible", False)

        if not admissible:
            decision = "defer"
            requires_human = True
            reasoning = "Consensus merge near threshold; requires quorum review"
        else:
            decision = "allow"
            requires_human = False
            reasoning = "Consensus merge admissible"

        receipt = await self.cge.append_ledger(
            mutation_class="derive" if decision == "allow" else "reject",
            actor=referee_actor,
            payload=merge_output,
            bcat=bcat,
            gcat=gcat,
        )

        return AdmissionResult(
            decision=decision,
            receipt=receipt,
            bcat=bcat,
            gcat=gcat,
            reasoning=reasoning,
            requires_human=requires_human,
        )

    def _is_deferrable(self, bcat: Dict, gcat: Dict) -> bool:
        """Check if scores are close enough to threshold to defer rather than deny."""
        margin = 0.1
        checks = [
            bcat.get("observability", 0) >= self.thresholds.get("observability_min", 0.6) - margin,
            bcat.get("context_stability", 0) >= self.thresholds.get("context_stability_min", 0.5) - margin,
            bcat.get("authority_clarity", 0) >= self.thresholds.get("authority_clarity_min", 0.5) - margin,
            bcat.get("risk", 1.0) <= self.thresholds.get("risk_max", 0.7) + margin,
        ]
        return sum(checks) >= 3
