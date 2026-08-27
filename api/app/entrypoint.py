"""Stable ASGI entrypoint for the governed bridge API.

The primary application is constructed in api.app.main. This compatibility
entrypoint mounts the existing governed style-experiment router exactly once
without mutating process-global builtins.
"""
from __future__ import annotations

from .main import app
from .governance.style_experiments import router as style_experiment_router

STYLE_ROUTER_STATE_KEY = "style_experiment_router_mounted"

if not getattr(app.state, STYLE_ROUTER_STATE_KEY, False):
    app.include_router(style_experiment_router)
    setattr(app.state, STYLE_ROUTER_STATE_KEY, True)

__all__ = ["app"]
