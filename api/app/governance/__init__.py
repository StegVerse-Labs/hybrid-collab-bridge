"""Governance package bootstrap.

This module installs the automatic /v1/run assessment middleware on the bridge
application as soon as FastAPI constructs it. Application configuration is owned
by api.app.main and is not mirrored through process-global builtins.
"""
from __future__ import annotations

from fastapi import FastAPI

_ORIGINAL_FASTAPI_INIT = FastAPI.__init__
_PATCH_FLAG = "_stegverse_governance_bootstrap_patched"


if not getattr(FastAPI, _PATCH_FLAG, False):
    def _governed_fastapi_init(self, *args, **kwargs):
        _ORIGINAL_FASTAPI_INIT(self, *args, **kwargs)
        if str(getattr(self, "title", "")).startswith("Hybrid Collab Bridge"):
            from .human_llm_run_hook import install_run_assessment_hook
            install_run_assessment_hook(self)

    FastAPI.__init__ = _governed_fastapi_init
    setattr(FastAPI, _PATCH_FLAG, True)
