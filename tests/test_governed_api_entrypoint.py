from __future__ import annotations

import builtins
import importlib
import sys


def test_entrypoint_imports_primary_app_and_mounts_style_routes(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")

    for name in ("api.app.entrypoint", "api.app.main"):
        sys.modules.pop(name, None)

    module = importlib.import_module("api.app.entrypoint")
    paths = {getattr(route, "path", None) for route in module.app.routes}

    assert "/health" in paths
    assert "/v1/run" in paths
    assert "/v1/interoperability/style-experiments/accommodation" in paths
    assert "/v1/interoperability/style-experiments/{experiment_id}" in paths
    assert not hasattr(builtins, "ADMIN_TOKEN")


def test_entrypoint_does_not_duplicate_style_routes():
    module = importlib.import_module("api.app.entrypoint")
    paths = [getattr(route, "path", None) for route in module.app.routes]
    assert paths.count("/v1/interoperability/style-experiments/accommodation") == 1
