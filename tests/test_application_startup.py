"""Regression coverage for application initialization and router configuration."""
from __future__ import annotations

import importlib


def test_application_imports_with_governance_routers_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_TOKEN", "startup-test-token")
    monkeypatch.setenv("HCB_CGE_PATH", str(tmp_path / "cge_light"))
    monkeypatch.setenv("HCB_SESSIONS_ROOT", str(tmp_path / "sessions"))
    monkeypatch.setenv("HCB_RECEIPT_SIGNING_KEY", "startup-test-signing-key")

    module = importlib.import_module("api.app.main")

    assert module.ADMIN_TOKEN == "startup-test-token"
    paths = {route.path for route in module.app.routes}
    assert "/health" in paths
    assert "/v1/interoperability/assessments" in paths
    assert "/v1/interoperability/replay/{assessment_id}" in paths
