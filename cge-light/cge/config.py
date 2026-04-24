from __future__ import annotations
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_repo_contract():
    return load_yaml(ROOT / "repo_contract.txt")


def load_repo_constitution():
    return load_yaml(ROOT / "repo_constitution.txt")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def getenv(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
