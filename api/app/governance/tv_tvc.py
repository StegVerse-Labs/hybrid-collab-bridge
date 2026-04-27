"""TV/TVC Secret Management — Ephemeral, Platform-Agnostic.

TrustVault (TV) + TrustVaultController (TVC) integration for:
- Ephemeral secret retrieval (short-lived, auto-rotated)
- Platform-agnostic credential handling
- Zero hardcoded secrets in files or env
- Automatic token refresh before expiry

Architecture:
    Bridge → TVC Request → TV Vault → Ephemeral Token → Use → Discard

No secret ever persists in:
- .env files
- providers.txt
- Source code
- Docker layers
- Session traces

Only TVC reference IDs persist (non-sensitive pointers).
"""
from __future__ import annotations
import os
import time
import json
import hashlib
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import httpx


@dataclass
class EphemeralCredential:
    """A short-lived credential from TV/TVC."""
    credential_id: str           # TV reference ID (non-sensitive)
    provider_type: str           # openai, anthropic, moonshot, etc.
    token: str                   # Actual secret (ephemeral)
    expires_at: float            # Unix timestamp
    scope: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    @property
    def ttl_seconds(self) -> float:
        return max(0, self.expires_at - time.time())


class TVCClient:
    """TrustVaultController client for ephemeral secret management.

    Modes:
    - "direct": TVC HTTP endpoint (StegVerse-org/TVC or local TVC)
    - "file": Local TV vault file (development/testing)
    - "env": Ephemeral env injection (CI/CD, containers)
    - "callback": User-provided callback (custom integration)
    """

    def __init__(
        self,
        tvc_endpoint: Optional[str] = None,
        tvc_api_key: Optional[str] = None,
        mode: str = "direct",
        callback: Optional[Callable[[str], Optional[EphemeralCredential]]] = None,
        default_ttl: int = 3600,  # 1 hour default
        refresh_buffer: int = 300,  # Refresh 5 min before expiry
    ):
        self.endpoint = tvc_endpoint or os.getenv("TVC_ENDPOINT")
        self.api_key = tvc_api_key or os.getenv("TVC_API_KEY")
        self.mode = mode
        self.callback = callback
        self.default_ttl = default_ttl
        self.refresh_buffer = refresh_buffer
        self._cache: Dict[str, EphemeralCredential] = {}

    async def get_credential(
        self,
        credential_id: str,
        provider_type: str,
        force_refresh: bool = False,
    ) -> Optional[EphemeralCredential]:
        """Retrieve ephemeral credential from TV/TVC.

        Args:
            credential_id: TV reference ID (e.g., "cred-openai-prod", "cred-anthropic-dev")
            provider_type: Provider type for validation
            force_refresh: Ignore cache and fetch fresh
        """
        # Check cache first
        if not force_refresh and credential_id in self._cache:
            cached = self._cache[credential_id]
            if not cached.is_expired and cached.ttl_seconds > self.refresh_buffer:
                return cached

        # Fetch from TVC
        credential = await self._fetch(credential_id, provider_type)
        if credential:
            self._cache[credential_id] = credential
        return credential

    async def _fetch(
        self,
        credential_id: str,
        provider_type: str,
    ) -> Optional[EphemeralCredential]:
        """Internal fetch from TVC."""
        if self.mode == "direct":
            return await self._fetch_direct(credential_id, provider_type)
        elif self.mode == "file":
            return self._fetch_file(credential_id, provider_type)
        elif self.mode == "env":
            return self._fetch_env(credential_id, provider_type)
        elif self.mode == "callback" and self.callback:
            return self.callback(credential_id)
        return None

    async def _fetch_direct(
        self,
        credential_id: str,
        provider_type: str,
    ) -> Optional[EphemeralCredential]:
        """Fetch from TVC HTTP endpoint."""
        if not self.endpoint:
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/vault/unseal",
                    json={
                        "credential_id": credential_id,
                        "provider_type": provider_type,
                        "requested_ttl": self.default_ttl,
                        "purpose": "hybrid-collab-bridge",
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                r.raise_for_status()
                data = r.json()

                return EphemeralCredential(
                    credential_id=credential_id,
                    provider_type=provider_type,
                    token=data["token"],
                    expires_at=data["expires_at"],
                    scope=data.get("scope", []),
                    metadata=data.get("metadata", {}),
                )
        except Exception as e:
            # Log but don't expose details
            print(f"[TVC] Failed to fetch {credential_id}: {type(e).__name__}")
            return None

    def _fetch_file(
        self,
        credential_id: str,
        provider_type: str,
    ) -> Optional[EphemeralCredential]:
        """Fetch from local TV vault file (development only)."""
        import pathlib

        vault_path = pathlib.Path(os.getenv("TV_VAULT_PATH", "./.tv/vault.json"))
        if not vault_path.exists():
            return None

        try:
            vault = json.loads(vault_path.read_text(encoding="utf-8"))
            entry = vault.get(credential_id)
            if not entry:
                return None

            return EphemeralCredential(
                credential_id=credential_id,
                provider_type=provider_type,
                token=entry["token"],
                expires_at=entry.get("expires_at", time.time() + self.default_ttl),
                scope=entry.get("scope", []),
                metadata=entry.get("metadata", {}),
            )
        except Exception:
            return None

    def _fetch_env(
        self,
        credential_id: str,
        provider_type: str,
    ) -> Optional[EphemeralCredential]:
        """Fetch from ephemeral environment (CI/CD injection)."""
        # Map credential_id to env var
        env_map = {
            "cred-openai": "EPHEMERAL_OPENAI_KEY",
            "cred-anthropic": "EPHEMERAL_ANTHROPIC_KEY",
            "cred-moonshot": "EPHEMERAL_MOONSHOT_KEY",
            "cred-google": "EPHEMERAL_GEMINI_KEY",
            "cred-xai": "EPHEMERAL_XAI_KEY",
            "cred-deepseek": "EPHEMERAL_DEEPSEEK_KEY",
            "cred-perplexity": "EPHEMERAL_PERPLEXITY_KEY",
        }

        env_var = env_map.get(credential_id)
        if not env_var:
            return None

        token = os.getenv(env_var)
        if not token:
            return None

        # Ephemeral env vars expire quickly (set by CI/CD)
        expiry = float(os.getenv(f"{env_var}_EXPIRES", time.time() + 900))  # 15 min default

        return EphemeralCredential(
            credential_id=credential_id,
            provider_type=provider_type,
            token=token,
            expires_at=expiry,
        )

    def invalidate(self, credential_id: str) -> None:
        """Explicitly invalidate a cached credential."""
        if credential_id in self._cache:
            del self._cache[credential_id]

    def invalidate_all(self) -> None:
        """Invalidate all cached credentials."""
        self._cache.clear()

    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status for monitoring."""
        return {
            "cached_count": len(self._cache),
            "entries": [
                {
                    "credential_id": c.credential_id,
                    "provider_type": c.provider_type,
                    "ttl_seconds": c.ttl_seconds,
                    "is_expired": c.is_expired,
                }
                for c in self._cache.values()
            ],
        }


class TVProviderAdapter:
    """Wraps any provider adapter with TV/TVC ephemeral credential handling.

    Usage:
        base_provider = AnthropicText("claude")
        tv_adapter = TVProviderAdapter(base_provider, tvc_client, "cred-anthropic")
        result = await tv_adapter.run(task)  # Auto-fetches ephemeral key
    """

    def __init__(
        self,
        base_provider: Any,
        tvc_client: TVCClient,
        credential_id: str,
    ):
        self.base = base_provider
        self.tvc = tvc_client
        self.credential_id = credential_id
        self._last_token: Optional[str] = None

    async def run(self, task: Any) -> Dict[str, Any]:
        """Run with ephemeral credential injection."""
        cred = await self.tvc.get_credential(
            self.credential_id,
            self.base.type,
        )

        if not cred or cred.is_expired:
            return {
                "error": f"No valid credential for {self.credential_id}",
                "action": "Request credential from TVC",
            }

        # Inject token into provider's headers
        self._inject_token(cred.token)
        self._last_token = cred.token

        try:
            result = await self.base.run(task)
            return result
        finally:
            # Optional: clear token from memory after use
            self._clear_token()

    def _inject_token(self, token: str) -> None:
        """Inject ephemeral token into provider."""
        # Provider-specific injection
        if hasattr(self.base, "headers"):
            if "x-api-key" in self.base.headers:
                self.base.headers["x-api-key"] = token
            elif "Authorization" in self.base.headers:
                self.base.headers["Authorization"] = f"Bearer {token}"
        elif hasattr(self.base, "api_key"):
            self.base.api_key = token

    def _clear_token(self) -> None:
        """Clear token from memory."""
        self._last_token = None
        if hasattr(self.base, "api_key"):
            self.base.api_key = ""

    def supports(self, task_type: str) -> bool:
        return self.base.supports(task_type)

    @property
    def name(self) -> str:
        return self.base.name

    @property
    def type(self) -> str:
        return self.base.type
