"""Admission gate: BCAT/GCAT evaluation before execution."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Literal
from dataclasses import dataclass, field

from .entity import EntityIdentity
from .cge_client import CGELightClient
from .governance_snapshot import build_governance_snapshot


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
    governance_snapshot: Dict[str, Any] = field(default_factory=dict)


class AdmissionGate:
    def __init__(self, cge_client: CGELightClient, constitution: Dict[str, Any]):
        self.cge = cge_client
        self.constitution = constitution
        self.thresholds = constitution.get("threshold_profiles", {}).get("standard", {})

    @staticmethod
    def _persist_snapshot(proposal: Dict[str, Any], snapshot: Dict[str, Any]) -> None:
        session_path = proposal.get("session_path")
        if not isinstance(session_path, str) or not session_path:
            return
        session_dir = Path(session_path)
        if not session_dir.exists() or not session_dir.is_dir():
            return
        path = session_dir / "08_commit_time_governance_snapshot.json"
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    async def admit_proposal(
        self,
        proposal: Dict[str, Any],
        actor: EntityIdentity,
        source: str = "hybrid-collab-bridge",
    ) -> AdmissionResult:
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
        snapshot = build_governance_snapshot(
            proposal=proposal,
            actor=actor.to_dict(),
            source=source,
            constitution=self.constitution,
            ingest_result=ingest_result,
            canonical_decision=decision,
            cge_path=self.cge.cge_path,
        )
        self._persist_snapshot(proposal, snapshot)

        return AdmissionResult(
            decision=decision,
            receipt=receipt,
            bcat=bcat,
            gcat=gcat,
            reasoning=reasoning,
            requires_human=requires_human,
            governance_snapshot=snapshot,
        )

    async def admit_consensus_merge(
        self,
        proposals: list,
        merge_output: Dict[str, Any],
        referee_actor: EntityIdentity,
    ) -> AdmissionResult:
        proposal = {
            "proposals_count": len(proposals),
            "merge_output": merge_output,
            "strategy": "consensus",
        }
        source = "hybrid-collab-bridge/consensus"
        ingest_result = await self.cge.ingest(
            payload=proposal,
            source=source,
            actor=referee_actor,
            mutation_class="derive",
        )

        bcat = ingest_result.get("bcat", {})
        gcat = ingest_result.get("gcat", {})
        admissible = ingest_result.get("admissible", False)

        if not admissible:
            decision: Decision = "defer"
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
        snapshot = build_governance_snapshot(
            proposal=proposal,
            actor=referee_actor.to_dict(),
            source=source,
            constitution=self.constitution,
            ingest_result=ingest_result,
            canonical_decision=decision,
            cge_path=self.cge.cge_path,
        )

        return AdmissionResult(
            decision=decision,
            receipt=receipt,
            bcat=bcat,
            gcat=gcat,
            reasoning=reasoning,
            requires_human=requires_human,
            governance_snapshot=snapshot,
        )

    def _is_deferrable(self, bcat: Dict, gcat: Dict) -> bool:
        margin = 0.1
        checks = [
            bcat.get("observability", 0) >= self.thresholds.get("observability_min", 0.6) - margin,
            bcat.get("context_stability", 0) >= self.thresholds.get("context_stability_min", 0.5) - margin,
            bcat.get("authority_clarity", 0) >= self.thresholds.get("authority_clarity_min", 0.5) - margin,
            bcat.get("risk", 1.0) <= self.thresholds.get("risk_max", 0.7) + margin,
        ]
        return sum(checks) >= 3
