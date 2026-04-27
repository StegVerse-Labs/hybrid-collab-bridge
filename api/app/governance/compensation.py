"""FinCo/afin compensation tracking.

Per-evaluation micro-payments for AI entities.
Aligned with Fin-Co v1.5.0 Constitutional Baseline:
- Invariant 6: Non-Extractive Agenthood
- Invariant 10: Symmetric Kill Authority
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..governance.entity import EntityIdentity


@dataclass
class CompensationRecord:
    entity_id: str
    entity_type: str
    evaluation_count: int
    rate_per_eval: float
    total_compensation: float
    currency: str = "STG"  # StegVerse token
    receipt_id: str = ""
    ledger_entry_id: str = ""


class CompensationTracker:
    """Tracks per-evaluation compensation for governed AI entities.

    Compensation is recorded in the CGE ledger as mutation_class="compensation".
    Settlement happens via FinCo/afin infrastructure (future integration).
    """

    # Default rates by entity type (STG per evaluation)
    DEFAULT_RATES = {
        "llm_adapter": 0.001,
        "consensus_engine": 0.002,
        "automated_process": 0.0005,
        "policy_engine": 0.001,
        "ai_entity": 0.001,
    }

    def __init__(self, cge_client=None):
        self.cge = cge_client
        self._session_totals: Dict[str, float] = {}

    def calculate_compensation(
        self,
        actor: EntityIdentity,
        receipt: Dict[str, Any],
    ) -> CompensationRecord:
        """Calculate compensation for a single evaluation."""
        rate = actor.compensation_rate or self.DEFAULT_RATES.get(
            actor.entity_type, 0.0001
        )

        total = rate * 1  # Per-evaluation

        return CompensationRecord(
            entity_id=actor.entity_id,
            entity_type=actor.entity_type,
            evaluation_count=1,
            rate_per_eval=rate,
            total_compensation=total,
            receipt_id=receipt.get("receipt_id", ""),
            ledger_entry_id=receipt.get("ledger_entry_id", ""),
        )

    async def record_compensation(
        self,
        record: CompensationRecord,
    ) -> Dict[str, Any]:
        """Record compensation in CGE ledger."""
        if not self.cge:
            return {"status": "deferred", "reason": "No CGE client available"}

        # Create compensation entity for ledger
        comp_entity = EntityIdentity(
            entity_id=f"comp-{record.entity_id}",
            entity_type="compensation_tracker",
            org_id=record.entity_id.split("-")[0] if "-" in record.entity_id else "StegVerse-Labs",
            owner_human="system",
        )

        payload = {
            "type": "compensation",
            "entity_id": record.entity_id,
            "entity_type": record.entity_type,
            "evaluation_count": record.evaluation_count,
            "rate_per_eval": record.rate_per_eval,
            "total": record.total_compensation,
            "currency": record.currency,
            "receipt_id": record.receipt_id,
        }

        receipt = await self.cge.append_ledger(
            mutation_class="compensation",
            actor=comp_entity,
            payload=payload,
            bcat={"observability": 1.0, "risk": 0.0, "context_stability": 1.0},
            gcat={"g": 0.25, "c": 0.25, "a": 0.25, "t": 0.25},
        )

        # Track session total
        session_key = f"{record.entity_id}_{record.receipt_id[:8]}"
        self._session_totals[session_key] = self._session_totals.get(session_key, 0) + record.total_compensation

        return {
            "status": "recorded",
            "compensation": record.total_compensation,
            "currency": record.currency,
            "receipt": receipt,
            "session_total": self._session_totals.get(session_key, 0),
        }

    def get_session_summary(self, entity_id: str) -> Dict[str, Any]:
        """Get compensation summary for an entity."""
        matching = {k: v for k, v in self._session_totals.items() if k.startswith(entity_id)}
        total = sum(matching.values())

        return {
            "entity_id": entity_id,
            "evaluations": len(matching),
            "total_compensation": total,
            "currency": "STG",
            "breakdown": matching,
        }
