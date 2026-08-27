"""Hybrid Collab Bridge application package bootstrap.

The primary application now resolves ADMIN_TOKEN in api.app.main before any
subordinate router configuration. No process-global builtins credential or
authorization fallback is installed by this package.
"""
from __future__ import annotations
