"""StegDB Ingestion Wiring.

Auto-pushes all CGE receipts and session traces to StegDB.
Configured via HCB_STEGDB_ENDPOINT and HCB_STEGDB_API_KEY.

Integration points:
- After every /v1/run → push final receipt + trace
- After every /v1/continue → push approval receipt
- Dashboard query → pull entity history from StegDB
"""
from __future__ import annotations
import os
from typing import Dict, Any

from .stegdb import StegDBClient
from .entity import EntityIdentity


class StegDBWiring:
    """Auto-wire StegDB ingestion into bridge operations."""

    def __init__(self):
        endpoint = os.getenv("HCB_STEGDB_ENDPOINT")
        api_key = os.getenv("HCB_STEGDB_API_KEY")

        if endpoint:
            self.client = StegDBClient(
                endpoint=endpoint,
                api_key=api_key,
                mode="direct",
            )
            self.enabled = True
        else:
            self.client = StegDBClient(mode="filesystem")
            self.enabled = bool(os.getenv("HCB_STEGDB_FILESYSTEM", "true"))

    async def push_run_result(
        self,
        session_path: str,
        final_receipt: Dict[str, Any],
        turns: list,
        bridge_entity: EntityIdentity,
    ) -> Dict[str, Any]:
        """Push complete run result to StegDB."""
        if not self.enabled:
            return {"status": "disabled"}

        payload = {
            "type": "bridge_run",
            "session_path": session_path,
            "final_receipt": final_receipt,
            "turn_count": len(turns),
            "experts": [t.who for t in turns],
            "decisions": [t.decision for t in turns],
        }

        return await self.client.ingest_receipt(
            receipt=final_receipt,
            actor=bridge_entity,
            source="hybrid-collab-bridge/run",
        )

    async def push_approval(
        self,
        approval_receipt: Dict[str, Any],
        approver: EntityIdentity,
    ) -> Dict[str, Any]:
        """Push quorum approval to StegDB."""
        if not self.enabled:
            return {"status": "disabled"}

        return await self.client.ingest_receipt(
            receipt=approval_receipt,
            actor=approver,
            source="hybrid-collab-bridge/approval",
        )

    async def query_entity_history(
        self,
        entity_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Query StegDB for entity operation history."""
        if not self.enabled:
            return {"status": "disabled"}

        return await self.client.query_entity_history(entity_id, limit)
