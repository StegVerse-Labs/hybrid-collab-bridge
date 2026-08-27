from __future__ import annotations

import builtins
import importlib
import sys


def test_entrypoint_imports_primary_app_and_mounts_style_routes(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")

    for name in ("api.app.entrypoint", "api.app.main"):
        sys.modules.pop(name, None)

    module = importlib.import_module("api.app.entrypoint")
    paths = set(module.app.openapi()["paths"])

    assert "/health" in paths
    assert "/v1/run" in paths
    assert "/v1/interoperability/style-experiments/accommodation" in paths
    assert "/v1/interoperability/style-experiments/{experiment_id}" in paths
    assert not hasattr(builtins, "ADMIN_TOKEN")


def test_entrypoint_style_router_mount_is_idempotent():
    module = importlib.import_module("api.app.entrypoint")
    before = len(module.app.routes)
    reloaded = importlib.reload(module)
    after = len(reloaded.app.routes)

    assert after == before
    paths = set(reloaded.app.openapi()["paths"])
    assert "/v1/interoperability/style-experiments/accommodation" in paths
