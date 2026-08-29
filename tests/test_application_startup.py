"""Regression coverage for application initialization and router configuration."""
from __future__ import annotations

import importlib
import sys


def test_application_imports_with_governance_routers_configured(monkeypatch, tmp_path):
    # A consumer-local admin bearer must not be materialized even if a legacy
    # deployment environment still supplies one.
    monkeypatch.setenv("ADMIN_TOKEN", "legacy-value-must-be-ignored")
    monkeypatch.setenv("HCB_CGE_PATH", str(tmp_path / "cge_light"))
    monkeypatch.setenv("HCB_SESSIONS_ROOT", str(tmp_path / "sessions"))
    monkeypatch.setenv("HCB_RECEIPT_SIGNING_KEY", "startup-test-signing-key")

    sys.modules.pop("api.app.main", None)
    module = importlib.import_module("api.app.main")

    assert not hasattr(module, "ADMIN_TOKEN")
    assert module.ADMIN_AUTH_STATE == "TVC_ADMITTED_ADMIN_AUTH_REQUIRED"
    paths = set(module.app.openapi()["paths"])
    assert "/health" in paths
    assert "/v1/interoperability/assessments" in paths
    assert "/v1/interoperability/replay/{assessment_id}" in paths
