import pytest
import os
import sys
from pathlib import Path

# Ensure cge_light is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cge_light"))

@pytest.fixture
def mock_env():
    """Clean environment for tests."""
    old = dict(os.environ)
    os.environ.update({
        "HCB_ORG_ID": "Test-Org",
        "HCB_CGE_MODE": "embedded",
        "HCB_OWNER_HUMAN": "test_human",
        "HCB_OWNER_AI": "test_ai",
        "ADMIN_TOKEN": "test-token",
    })
    os.environ.pop("HCB_CGE_ENDPOINT", None)
    yield
    os.environ.clear()
    os.environ.update(old)

@pytest.fixture
def sample_payload():
    return {
        "type": "test_payload",
        "content": "Hello StegVerse",
        "timestamp": 1234567890,
    }


@pytest.fixture
def no_remote_cge(monkeypatch):
    """Fail the test if anything opens an HTTP client while CGE is exercised."""
    import httpx

    contacted = []

    class _Forbidden:
        def __init__(self, *args, **kwargs):
            contacted.append((args, kwargs))
            raise AssertionError("remote CGE contacted; embedded mode is the only mode")

    monkeypatch.setattr(httpx, "AsyncClient", _Forbidden)
    monkeypatch.setattr(httpx, "Client", _Forbidden)
    monkeypatch.setenv("HCB_CGE_ENDPOINT", "http://remote-cge.invalid")
    return contacted
