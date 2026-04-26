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
