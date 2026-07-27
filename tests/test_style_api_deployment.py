from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_render_blueprint_targets_bounded_style_api():
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = blueprint["services"]
    assert len(services) == 1
    service = services[0]
    assert service["runtime"] == "docker"
    assert service["dockerfilePath"] == "./Dockerfile.style-api"
    assert service["healthCheckPath"] == "/health"
    assert service["disk"]["mountPath"] == "/var/data"
    env = {item["key"]: item.get("value") for item in service["envVars"]}
    assert env["HCB_STYLE_EXPERIMENT_ROOT"] == "/var/data/style-experiments"


def test_container_runs_dedicated_style_api_as_non_root():
    dockerfile = (ROOT / "Dockerfile.style-api").read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in dockerfile
    assert "USER appuser" in dockerfile
    assert "uvicorn api.app.style_api:app" in dockerfile
    assert "--host 0.0.0.0" in dockerfile
    assert "${PORT:-8000}" in dockerfile


def test_runtime_dependency_surface_is_minimal():
    dependencies = {
        line.strip().split("[", 1)[0].split(">", 1)[0].split("=", 1)[0]
        for line in (ROOT / "requirements-style-api.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert dependencies == {"fastapi", "pydantic", "uvicorn"}
