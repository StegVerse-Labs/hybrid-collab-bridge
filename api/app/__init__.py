"""Hybrid Collab Bridge application package bootstrap.

The primary application now resolves its admin configuration in api.app.main
before subordinate router configuration. This package installs no process-global
builtins fallback.
"""
from __future__ import annotations
