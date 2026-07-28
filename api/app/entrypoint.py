"""Stable ASGI entrypoint for the governed bridge API.

This module resolves legacy initialization order before importing ``main`` and
mounts the governed style-experiment router on the primary application.
"""
from __future__ import annotations

import builtins
import os

# ``api.app.main`` historically referenced ADMIN_TOKEN before assigning it in
# module scope. Python falls back to builtins for unresolved globals, allowing
# this compatibility shim to preserve the existing module while ensuring a
# deterministic import. The main module later assigns its own ADMIN_TOKEN.
builtins.ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

from .main import app  # noqa: E402
from .governance.style_experiments import router as style_experiment_router  # noqa: E402


def _has_route(path: str) -> bool:
    return any(getattr(route, "path", None) == path for route in app.routes)


STYLE_SUBMIT_PATH = "/v1/interoperability/style-experiments/accommodation"
if not _has_route(STYLE_SUBMIT_PATH):
    app.include_router(style_experiment_router)

# Remove the compatibility value once the application has completed import.
try:
    del builtins.ADMIN_TOKEN
except AttributeError:
    pass

__all__ = ["app"]
