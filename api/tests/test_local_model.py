import subprocess

import pytest

from app.providers.local_model import LocalModelBuilder
from app.providers.local_runtime import LocalModel


def test_plan_requires_installed_base_and_is_credential_free():
    builder = LocalModelBuilder(command_finder=lambda _: "/usr/bin/ollama")
    plan = builder.plan(
        [LocalModel(name="base-local:1")],
        base_model="base-local:1",
        target_model="stegverse-local:v1",
    )
    assert plan.base_model == "base-local:1"
    assert plan.target_model == "stegverse-local:v1"
    assert plan.definition_hash.startswith("sha256:")
    assert "API_KEY" not in plan.modelfile
    assert "credential" in plan.system_prompt.lower()
    assert "FROM base-local:1" in plan.modelfile


def test_plan_refuses_uninstalled_base():
    builder = LocalModelBuilder()
    with pytest.raises(RuntimeError, match="not present"):
        builder.plan([], "missing:1", "stegverse-local:v1")


def test_plan_refuses_injection_names():
    builder = LocalModelBuilder()
    with pytest.raises(ValueError):
        builder.plan([LocalModel(name="base:1")], "base:1\nSYSTEM bad", "stegverse-local:v1")


def test_build_uses_fixed_argv_without_shell():
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    builder = LocalModelBuilder(
        command_finder=lambda _: "/opt/ollama",
        runner=runner,
    )
    plan = builder.plan(
        [LocalModel(name="base-local:1")],
        "base-local:1",
        "stegverse-local:v1",
    )
    receipt = builder.build(plan)

    argv, kwargs = calls[0]
    assert argv[:3] == ["/opt/ollama", "create", "stegverse-local:v1"]
    assert kwargs["shell"] is False
    assert receipt.built is True
    assert receipt.exit_code == 0


def test_build_fails_closed_without_ollama():
    builder = LocalModelBuilder(command_finder=lambda _: None)
    plan = builder.plan(
        [LocalModel(name="base-local:1")],
        "base-local:1",
        "stegverse-local:v1",
    )
    with pytest.raises(RuntimeError, match="blocked"):
        builder.build(plan)
