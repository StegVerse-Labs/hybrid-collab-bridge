"""TV/TVC compatibility boundary for hybrid-collab-bridge.

The historical bridge-local credential delivery model is retired.

Current authority:
- credential/protected-value processing remains inside TV/TVC;
- this consumer repository receives no raw or ephemeral provider credential;
- no file/env/direct secret fallback is permitted here;
- external provider execution requires an already-admitted TV/TVC provider route;
- this module grants no execution or credential authority.

The class names remain as compatibility surfaces for callers that imported the
legacy bridge module. They intentionally cannot transport provider secrets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


BLOCKED_REASON = "TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED"


@dataclass(frozen=True)
class EphemeralCredential:
    """Non-secret compatibility record.

    Historical versions carried a `token` field. Current bridge consumers may
    retain only non-secret credential identity metadata; credential material is
    never returned to this process.
    """

    credential_id: str
    provider_type: str
    expires_at: float = 0.0
    scope: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    credential_material_present: bool = False

    @property
    def is_expired(self) -> bool:
        return True

    @property
    def ttl_seconds(self) -> float:
        return 0.0


class TVCClient:
    """Compatibility client that cannot retrieve protected values.

    Legacy constructor arguments are accepted so older callers fail closed
    rather than crashing during import/startup. Protected inputs are not
    retained, cached, exported, or used.
    """

    def __init__(
        self,
        tvc_endpoint: Optional[str] = None,
        tvc_api_key: Optional[str] = None,
        mode: str = "admitted-route-only",
        callback: Any = None,
        default_ttl: int = 0,
        refresh_buffer: int = 0,
    ):
        self.endpoint = tvc_endpoint
        self.api_key = None
        self.mode = "admitted-route-only"
        self.default_ttl = 0
        self.refresh_buffer = 0
        self._cache: Dict[str, EphemeralCredential] = {}

    async def get_credential(
        self,
        credential_id: str,
        provider_type: str,
        force_refresh: bool = False,
    ) -> None:
        return None

    async def get_credential_with_fallback(
        self,
        credential_id: str,
        provider_type: str,
        env_fallback: Optional[str] = None,
    ) -> None:
        return None

    def invalidate(self, credential_id: str) -> None:
        self._cache.pop(credential_id, None)

    def invalidate_all(self) -> None:
        self._cache.clear()

    def get_cache_status(self) -> Dict[str, Any]:
        return {
            "state": "BLOCKED",
            "reason": BLOCKED_REASON,
            "cached_count": 0,
            "entries": [],
            "credential_material_present": False,
            "authority_effect": False,
        }


class TVProviderAdapter:
    """Compatibility wrapper that never injects provider credentials."""

    def __init__(
        self,
        base_provider: Any,
        tvc_client: TVCClient,
        credential_id: str,
    ):
        self.base = base_provider
        self.tvc = tvc_client
        self.credential_id = credential_id

    async def run(self, task: Any) -> Dict[str, Any]:
        return {
            "state": "BLOCKED",
            "error": BLOCKED_REASON,
            "provider": self.name,
            "provider_type": self.type,
            "credential_material_present": False,
            "provider_execution_performed": False,
            "authority_effect": False,
        }

    def supports(self, task_type: str) -> bool:
        return self.base.supports(task_type)

    @property
    def name(self) -> str:
        return self.base.name

    @property
    def type(self) -> str:
        return self.base.type
