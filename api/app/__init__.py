"""Hybrid Collab Bridge application package bootstrap.

`app.main` historically configured subordinate routers before assigning its module-level
ADMIN_TOKEN. Python falls back to builtins for unresolved globals, so this compatibility
bootstrap makes the environment-derived token available during that early import. The
main module later assigns the same value normally.
"""
from __future__ import annotations

import builtins
import os

if not hasattr(builtins, "ADMIN_TOKEN"):
    builtins.ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
