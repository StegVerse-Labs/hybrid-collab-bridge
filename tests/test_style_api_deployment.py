from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hosted_deployment_surfaces_are_removed():
    # render.yaml (hosted Render service) and Dockerfile.style-api were removed
    # under HCB-VERSIONED-CONTRACT-038: the style API needs no external machine.
    for removed in ("render.yaml", "Dockerfile.style-api"):
        assert not (ROOT / removed).exists(), removed


def test_runtime_dependency_surface_is_minimal():
    dependencies = {
        line.strip().split("[", 1)[0].split(">", 1)[0].split("=", 1)[0]
        for line in (ROOT / "requirements-style-api.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert dependencies == {"fastapi", "pydantic", "uvicorn"}
