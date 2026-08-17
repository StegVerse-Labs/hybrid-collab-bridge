"""Compatibility shim for the canonical governed provider discovery engine.

The implementation lives in :mod:`app.governance.discovery`. Keeping this
module as a thin re-export prevents older imports from retaining a second
credential-discovery or local-runtime implementation.
"""
from __future__ import annotations

from ..governance.discovery import DiscoveryResult, ProviderDiscoveryEngine

__all__ = ["DiscoveryResult", "ProviderDiscoveryEngine"]
