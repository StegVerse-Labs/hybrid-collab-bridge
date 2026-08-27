"""Regression guards for retired hosted credential/control-plane authority."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_connectivity_workflow_has_no_hosted_github_token_or_repo_mutation():
    text = _text(".github/workflows/ai-entity-connectivity.yml")
    assert "secrets.GITHUB_TOKEN" not in text
    assert "GH_TOKEN:" not in text
    assert "contents: write" not in text
    assert "git push" not in text
    assert "repository_mutation_performed" in text


def test_delegation_workflow_has_no_hosted_transport_token_or_repo_mutation():
    text = _text(".github/workflows/transport-delegation-outbox.yml")
    assert "STEGVERSE_TRANSPORT_TOKEN" not in text
    assert "${{ secrets." not in text
    assert "contents: write" not in text
    assert "git push" not in text
    assert "TVC_ADMITTED_TRANSPORT_REQUIRED" in text


def test_consumer_transport_script_cannot_bearer_authorize_or_write_github():
    text = _text("scripts/transport_delegation_outbox.py")
    assert "Authorization" not in text
    assert "Bearer " not in text
    assert "api.github.com" not in text
    assert "urllib.request" not in text
    assert '"consumer_token_accepted": False' in text
    assert '"transport_performed": False' in text
