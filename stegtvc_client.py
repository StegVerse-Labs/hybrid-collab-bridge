"""Minimal StegTVC compatibility client for hybrid-collab-bridge.

This module intentionally provides a small, stable public function:
    stegtvc_resolve(use_case, module, importance="normal", **kwargs)

The diagnostic workflow imports that function directly.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict


def stegtvc_resolve(
    use_case: str,
    module: str,
    importance: str = "normal",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Resolve a StegTVC request into a deterministic diagnostic record.

    This is intentionally fail-closed for missing required fields, but it does
    not require external network access. It gives the workflow a stable import
    and a useful connectivity/self-check payload.
    """

    if not use_case:
        raise ValueError("use_case is required")

    if not module:
        raise ValueError("module is required")

    result: Dict[str, Any] = {
        "status": "ok",
        "resolved": True,
        "use_case": use_case,
        "module": module,
        "importance": importance or "normal",
        "client": "stegtvc_client",
        "mode": os.environ.get("STEGTVC_MODE", "local-diagnostic"),
        "timestamp_unix": int(time.time()),
    }

    if kwargs:
        result["metadata"] = dict(kwargs)

    return result


def resolve(
    use_case: str,
    module: str,
    importance: str = "normal",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Backward-compatible alias for callers that expect resolve()."""

    return stegtvc_resolve(
        use_case=use_case,
        module=module,
        importance=importance,
        **kwargs,
    )


__all__ = ["stegtvc_resolve", "resolve"]
