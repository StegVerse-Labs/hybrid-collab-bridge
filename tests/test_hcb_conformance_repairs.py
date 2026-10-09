"""Stdlib checks for the #38 conformance repairs (HCB-VERSIONED-CONTRACT-038)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class ConformanceRepairTests(unittest.TestCase):
    def test_version_is_single_valued(self):
        version = _read("VERSION").strip()
        self.assertRegex(_read("README.md"), r"(?m)^# hybrid-collab-bridge " + re.escape(version) + r"$")
        main = _read("api/app/main.py")
        self.assertIn(f'version="{version}"', main)
        self.assertIn(f'"version": "{version}"', main)
        self.assertNotIn("1.0.0", main)

    def test_single_canonical_handoff(self):
        pointer = _read("docs/HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md")
        self.assertIn("no longer a source of truth", pointer)
        self.assertLess(len(pointer.splitlines()), 15)
        canonical = _read("HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md")
        self.assertIn("HCB-VERSIONED-CONTRACT-038", canonical)
        self.assertIn("single canonical handoff", canonical)

    def test_no_bare_non_allow_markers_or_receiver_waits(self):
        canonical = _read("HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md")
        self.assertNotRegex(canonical, r"NOT[ _]OBSERVED")
        self.assertNotRegex(canonical, r"(?m)^state: BLOCKED$")
        self.assertNotIn("Until that exists, protected HCB API operations remain unavailable", canonical)
        blocks = re.findall(r"```text\n(disposition: (?:DENY|FAIL_CLOSED)\n.*?)```", canonical, re.S)
        self.assertGreaterEqual(len(blocks), 4)
        for block in blocks:
            for key in SIX_FIELDS:
                self.assertRegex(block, rf"(?m)^{key}: \S", key)

    def test_readme_labels_legacy_and_not_required_surfaces(self):
        readme = _read("README.md")
        for surface in ("admission.py", "cge-light/", "/v1/continue", "requires_human"):
            self.assertRegex(readme, rf"\|[^\n]*{re.escape(surface)}[^\n]*\| `LEGACY_ISOLATE`")
        for surface in ("render.yaml", "infra/docker-compose.yml", "HCB_STEGDB_ENDPOINT", "PUBLISHER_ENDPOINT"):
            self.assertRegex(readme, rf"\|[^\n]*{re.escape(surface)}[^\n]*\| `REMOVED`")

    def test_removed_external_service_surfaces_stay_removed(self):
        for removed in (
            "render.yaml",
            "Dockerfile.style-api",
            "infra/docker-compose.yml",
            "infra/Dockerfile",
            "api/dockerfile",
            "api/app/governance/stegdb.py",
            "api/app/governance/stegdb_wiring.py",
            "api/app/governance/publisher.py",
            "api/app/providers/stegdb.py",
            "app/main.py",
        ):
            self.assertFalse((ROOT / removed).exists(), removed)
        main = _read("api/app/main.py")
        for marker in ("StegDB", "STEGDB", "PublisherClient", "PUBLISHER_ENDPOINT", "/v1/publish/", "/v1/stegdb/"):
            self.assertNotIn(marker, main)
        for workflow in (ROOT / ".github/workflows").glob("*.yml"):
            self.assertNotIn("docker build", workflow.read_text(encoding="utf-8"), workflow.name)

    def test_reconcile_workflow_skips_no_op_commits(self):
        workflow = _read(".github/workflows/reconcile-internal-adapter.yml")
        commit_step = workflow.split("Commit reconciled runtime and state", 1)[1]
        self.assertIn("if: github.ref == 'refs/heads/main'", commit_step.split("run: |", 1)[0])
        guard = commit_step.index("changes_applied")
        self.assertLess(guard, commit_step.index("git commit"))
        state = json.loads(_read("state/internal_adapter_reconciliation.json"))
        self.assertIn("changes_applied", state)


if __name__ == "__main__":
    unittest.main()
