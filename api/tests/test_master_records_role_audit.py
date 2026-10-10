"""Master Records role audit: every occurrence must match the canonical role.

Master Records only records released organization batch receipts downstream; it is
not an authority, gate, custody holder, or runtime reality. See
docs/MASTER_RECORDS_ROLE.md and data/master-records-role-audit.json.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "data" / "master-records-role-audit.json"
PATTERN = re.compile(r"master[-_ ]?records?", re.IGNORECASE)
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
ALLOWED_AFTER = {"PROPER", "HISTORICAL_EVIDENCE", "NAMING_ONLY"}


def _audit():
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def _current_hits(excluded):
    hits = Counter()
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_DIRS.intersection(path.relative_to(ROOT).parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in excluded:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            if PATTERN.search(line):
                hits[(rel, line.strip())] += 1
    return hits


def test_audit_classifications_are_canonical():
    audit = _audit()
    allowed = set(audit["classifications"])
    for entry in audit["before"] + audit["after"]:
        assert entry["classification"] in allowed
    for entry in audit["before"]:
        if entry["classification"].startswith("IMPROPER"):
            assert entry["remediation"] == "REMEDIATED", entry
    for entry in audit["after"]:
        assert entry["classification"] in ALLOWED_AFTER, entry


def test_every_current_occurrence_is_audited_and_not_improper():
    audit = _audit()
    audited = Counter((e["file"], e["text"]) for e in audit["after"])
    current = _current_hits(set(audit["excluded_paths"]))
    unaudited = current - audited
    assert not unaudited, (
        "Unaudited Master Records occurrences; classify them in "
        f"data/master-records-role-audit.json: {sorted(unaudited)}"
    )


def test_historical_evidence_is_unedited():
    audit = _audit()
    for rel, digest in audit["historical_evidence_sha256"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel


def test_discovery_does_not_list_master_records_as_authority():
    from app.governance.discovery import ProviderDiscoveryEngine

    result = ProviderDiscoveryEngine()._sovereign_local_result()
    rendered = json.dumps([result.instructions, result.config_template]).lower()
    assert not PATTERN.search(rendered)
