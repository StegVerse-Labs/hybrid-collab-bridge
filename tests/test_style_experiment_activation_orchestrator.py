from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "run_style_experiment_activation.py"
spec = importlib.util.spec_from_file_location("run_style_experiment_activation", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def seed_packet(root: Path) -> None:
    (root / "packet.json").write_text(json.dumps({"experiment_id": "HIL-REAL-001"}), encoding="utf-8")


def successful_runner(command: list[str], cwd: Path, env: dict[str, str]):
    if "verify_style_experiment_packet.py" in command[1]:
        Path(command[command.index("--output") + 1]).write_text(
            json.dumps({"experiment_id": "HIL-REAL-001", "execution_admissible": True, "publication_admissible": False}),
            encoding="utf-8",
        )
    elif "build_style_experiment_execution_plan.py" in command[1]:
        Path(command[command.index("--output") + 1]).write_text(
            json.dumps({"experiment_id": "HIL-REAL-001", "execution_admissible": True, "publication_admissible": False}),
            encoding="utf-8",
        )
    elif "build_style_experiment_evidence_bundle.py" in command[1]:
        root = Path(command[2])
        (root / "manifest.json").write_text(
            json.dumps({"experiment_id": "HIL-REAL-001", "verification_admissible": True, "publication_admissible": False}),
            encoding="utf-8",
        )
    return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")


def test_activation_records_ordered_transitions_and_preserves_publication_separation(tmp_path: Path):
    seed_packet(tmp_path)
    journal, errors = module.activate(ROOT, tmp_path, runner=successful_runner, env={"HCB_STYLE_RECEIPT_KEY": "test"})
    assert errors == []
    assert journal["status"] == "COMPLETE"
    assert journal["execution_admissible"] is True
    assert journal["publication_admissible"] is False
    assert [row["transition_id"] for row in journal["transitions"]] == [
        "verify_packet",
        "build_execution_plan",
        "build_evidence_bundle",
        "verify_evidence_bundle",
    ]
    assert all(row["status"] == "PASS" for row in journal["transitions"])


def test_activation_stops_on_first_failed_transition(tmp_path: Path):
    seed_packet(tmp_path)
    calls: list[str] = []

    def runner(command: list[str], cwd: Path, env: dict[str, str]):
        calls.append(command[1])
        return subprocess.CompletedProcess(command, 7, stdout="", stderr="denied")

    journal, errors = module.activate(ROOT, tmp_path, runner=runner)
    assert journal["status"] == "BLOCKED"
    assert len(journal["transitions"]) == 1
    assert journal["transitions"][0]["status"] == "FAIL_CLOSED"
    assert errors == ["verify_packet returned 7", f"verify_packet did not create {tmp_path / 'readiness-report.json'}"]
    assert len(calls) == 1


def test_activation_blocks_when_command_claims_success_without_required_output(tmp_path: Path):
    seed_packet(tmp_path)

    def runner(command: list[str], cwd: Path, env: dict[str, str]):
        return subprocess.CompletedProcess(command, 0, stdout="claimed success", stderr="")

    journal, errors = module.activate(ROOT, tmp_path, runner=runner)
    assert journal["status"] == "BLOCKED"
    assert "did not create" in errors[0]


def test_activation_requires_packet_before_any_transition(tmp_path: Path):
    called = False

    def runner(command: list[str], cwd: Path, env: dict[str, str]):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    journal, errors = module.activate(ROOT, tmp_path, runner=runner)
    assert journal["status"] == "BLOCKED"
    assert errors == ["packet.json is required before activation"]
    assert journal["transitions"] == []
    assert called is False


def test_activation_does_not_infer_publication_from_execution(tmp_path: Path):
    seed_packet(tmp_path)

    def runner(command: list[str], cwd: Path, env: dict[str, str]):
        result = successful_runner(command, cwd, env)
        if "build_style_experiment_execution_plan.py" in command[1]:
            Path(command[command.index("--output") + 1]).write_text(
                json.dumps({"execution_admissible": True, "publication_admissible": True}), encoding="utf-8"
            )
        return result

    journal, errors = module.activate(ROOT, tmp_path, runner=runner)
    assert errors == []
    assert journal["execution_admissible"] is True
    assert journal["publication_admissible"] is False
