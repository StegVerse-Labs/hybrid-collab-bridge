"""StegDB ingestion integration.

Pushes CGE receipts and structured traces to StegDB for:
- Canonical audit trail
- Cross-org monitoring
- Entity sandbox validation
- Materialized state reconstruction
"""
from __future__ import annotations
import os
import json
import time
from typing import Dict, Any, Optional
import httpx

from ..governance.entity import EntityIdentity


class StegDBClient:
    """Client for StegDB ingestion.

    Modes:
    - "direct": POST to StegDB HTTP endpoint
    - "filesystem": Write to shared volume (for local StegDB)
    - "queue": Buffer in memory, flush periodically
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        mode: str = "direct",
        flush_interval: int = 10,
    ):
        self.endpoint = endpoint or os.getenv("HCB_STEGDB_ENDPOINT")
        self.api_key = api_key or os.getenv("HCB_STEGDB_API_KEY")
        self.mode = mode
        self.flush_interval = flush_interval
        self._buffer: list = []
        self._last_flush = time.time()

    async def ingest_receipt(
        self,
        receipt: Dict[str, Any],
        actor: EntityIdentity,
        source: str = "hybrid-collab-bridge",
    ) -> Dict[str, Any]:
        """Ingest a CGE receipt into StegDB."""
        payload = {
            "type": "cge_receipt",
            "source": source,
            "actor": actor.to_dict(),
            "receipt": receipt,
            "timestamp": int(time.time()),
            "org_id": actor.org_id,
        }

        if self.mode == "direct":
            return await self._post_direct(payload)
        elif self.mode == "filesystem":
            return self._write_filesystem(payload)
        else:
            self._buffer.append(payload)
            if time.time() - self._last_flush > self.flush_interval:
                return await self._flush_buffer()
            return {"status": "buffered", "count": len(self._buffer)}

    async def ingest_trace(
        self,
        trace: Dict[str, Any],
        session_path: str,
        actor: EntityIdentity,
    ) -> Dict[str, Any]:
        """Ingest a session trace into StegDB."""
        payload = {
            "type": "session_trace",
            "source": "hybrid-collab-bridge",
            "actor": actor.to_dict(),
            "session_path": session_path,
            "trace": trace,
            "timestamp": int(time.time()),
            "org_id": actor.org_id,
        }

        if self.mode == "direct":
            return await self._post_direct(payload)
        elif self.mode == "filesystem":
            return self._write_filesystem(payload)
        else:
            self._buffer.append(payload)
            return {"status": "buffered", "count": len(self._buffer)}

    async def _post_direct(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.endpoint:
            return {"error": "No StegDB endpoint configured"}

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/ingest",
                    json=payload,
                    headers=headers,
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"error": str(e), "fallback": "filesystem"}

    def _write_filesystem(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Write to shared volume for local StegDB pickup."""
        import pathlib

        stegdb_path = pathlib.Path("/shared/stegdb/inbox")
        stegdb_path.mkdir(parents=True, exist_ok=True)

        filename = f"{payload['type']}_{payload['timestamp']}_{payload['actor']['entity_id']}.json"
        filepath = stegdb_path / filename

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

        return {"status": "written", "path": str(filepath)}

    async def _flush_buffer(self) -> Dict[str, Any]:
        if not self._buffer:
            return {"status": "empty"}

        results = []
        for payload in self._buffer:
            result = await self._post_direct(payload)
            results.append(result)

        self._buffer.clear()
        self._last_flush = time.time()

        return {
            "status": "flushed",
            "count": len(results),
            "results": results,
        }

    async def query_entity_history(
        self,
        entity_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Query StegDB for an entity's operation history."""
        if not self.endpoint:
            return {"error": "No StegDB endpoint configured"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(
                    f"{self.endpoint}/v1/query/entity/{entity_id}",
                    params={"limit": limit},
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            return {"error": str(e)}
