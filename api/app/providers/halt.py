"""Emergency Halt — Circuit breaker for quorum-triggered shutdown.

Constitutional requirement: any 2 of [human_operator, ai_entity, policy_engine]
can trigger emergency halt.

Aligned with Fin-Co Invariant 10: Symmetric Kill Authority.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..governance.entity import EntityIdentity
from ..governance.cge_client import CGELightClient


@dataclass
class HaltRecord:
    halt_id: str
    triggered_by: str
    triggerer_type: str
    timestamp: float
    reason: str
    quorum_met: bool
    second_approver: Optional[str] = None
    status: str = "active"  # active | lifted


class EmergencyHalt:
    """Circuit breaker for emergency shutdown.

    Activation requires quorum per constitution:
    - emergency_halt: any 2 of [human_operator, ai_entity, policy_engine]
    """

    def __init__(self, cge_client: CGELightClient, constitution: Dict[str, Any]):
        self.cge = cge_client
        self.constitution = constitution
        self._halted: bool = False
        self._halt_record: Optional[HaltRecord] = None
        self._pending_approvals: Dict[str, str] = {}  # entity_id -> type

    @property
    def is_halted(self) -> bool:
        return self._halted

    async def request_halt(
        self,
        requester: EntityIdentity,
        reason: str,
    ) -> Dict[str, Any]:
        """Request emergency halt. May activate immediately or await second approval."""

        quorum_rules = self.constitution.get("quorum_rules", {})
        emergency_rule = quorum_rules.get("emergency_halt", {})
        required_types = emergency_rule.get("required", [])
        min_count = emergency_rule.get("min_count", 2)
        pairing_rule = emergency_rule.get("pairing_rule", "any_two_of_three")

        # Check if requester is authorized
        if requester.entity_type not in required_types:
            return {
                "status": "denied",
                "reason": f"Entity type {requester.entity_type} cannot request halt",
                "authorized_types": required_types,
            }

        # Record pending approval
        self._pending_approvals[requester.entity_id] = requester.entity_type

        # Check if quorum is met
        unique_types = set(self._pending_approvals.values())

        if pairing_rule == "any_two_of_three":
            quorum_met = len(self._pending_approvals) >= min_count
        else:
            quorum_met = False

        if quorum_met:
            # Activate halt
            self._halted = True
            self._halt_record = HaltRecord(
                halt_id=f"halt-{int(time.time())}",
                triggered_by=requester.entity_id,
                triggerer_type=requester.entity_type,
                timestamp=time.time(),
                reason=reason,
                quorum_met=True,
                second_approver=list(self._pending_approvals.keys())[-1],
            )

            # Record in ledger
            await self.cge.append_ledger(
                mutation_class="emergency_halt",
                actor=requester,
                payload={
                    "halt_id": self._halt_record.halt_id,
                    "reason": reason,
                    "quorum": list(self._pending_approvals.items()),
                },
                bcat={"observability": 1.0, "risk": 0.0, "authority_clarity": 1.0},
                gcat={"g": 0.25, "c": 0.25, "a": 0.25, "t": 0.25},
            )

            return {
                "status": "halted",
                "halt_id": self._halt_record.halt_id,
                "reason": reason,
                "quorum": self._pending_approvals,
                "message": "Emergency halt ACTIVE. All operations suspended.",
            }
        else:
            # Awaiting second approval
            return {
                "status": "pending",
                "reason": reason,
                "requester": requester.entity_id,
                "awaiting": f"{min_count - len(self._pending_approvals)} more approval(s)",
                "authorized_to_approve": [t for t in required_types if t != requester.entity_type],
                "message": "Halt request recorded. Awaiting second approver.",
            }

    async def lift_halt(
        self,
        requester: EntityIdentity,
        reason: str,
    ) -> Dict[str, Any]:
        """Lift emergency halt. Requires same quorum as activation."""

        if not self._halted:
            return {"status": "no_halt", "message": "No active halt to lift"}

        # For lifting, require the same quorum
        quorum_rules = self.constitution.get("quorum_rules", {})
        emergency_rule = quorum_rules.get("emergency_halt", {})
        required_types = emergency_rule.get("required", [])

        if requester.entity_type not in required_types:
            return {
                "status": "denied",
                "reason": f"Entity type {requester.entity_type} cannot lift halt",
            }

        # Record lift in ledger
        await self.cge.append_ledger(
            mutation_class="lift_halt",
            actor=requester,
            payload={
                "halt_id": self._halt_record.halt_id if self._halt_record else "unknown",
                "reason": reason,
                "lifted_by": requester.entity_id,
            },
            bcat={"observability": 1.0, "risk": 0.0, "authority_clarity": 1.0},
            gcat={"g": 0.25, "c": 0.25, "a": 0.25, "t": 0.25},
        )

        self._halted = False
        self._pending_approvals.clear()
        old_record = self._halt_record
        self._halt_record = None

        return {
            "status": "lifted",
            "halt_id": old_record.halt_id if old_record else "unknown",
            "reason": reason,
            "message": "Emergency halt LIFTED. Operations resuming.",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current halt status."""
        return {
            "halted": self._halted,
            "halt_record": {
                "halt_id": self._halt_record.halt_id,
                "triggered_by": self._halt_record.triggered_by,
                "reason": self._halt_record.reason,
                "timestamp": self._halt_record.timestamp,
                "quorum_met": self._halt_record.quorum_met,
            } if self._halt_record else None,
            "pending_approvals": self._pending_approvals,
        }
