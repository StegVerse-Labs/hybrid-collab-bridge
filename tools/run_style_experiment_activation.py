#!/usr/bin/env python3
"""Execute the governed style-experiment activation chain fail-closed.

This command does not generate model outputs. It starts only after receipt-bound
artifacts exist, records every transition, stops on the first failed gate, and
produces a journal suitable for inclusion in the final evidence bundle.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

CommandRunner = Callable[[list[str], Path, dict[str, str]], subprocess.CompletedProcess[str]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_runner(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_specs(repo_root: Path, experiment_root: Path) -> list[dict[str, Any]]:
    py = sys.executable
    packet = experiment_root / "packet.json"
    readiness = experiment_root / "readiness-report.json"
    plan = experiment_root / "execution-plan.json"
    manifest = experiment_root / "manifest.json"
    return [
        {
            "transition_id": "verify_packet",
            "command": [py, str(repo_root / "tools/verify_style_experiment_packet.py"), str(packet), "--output", str(readiness)],
            "required_output": readiness,
        },
        {
            "transition_id": "build_execution_plan",
            "command": [py, str(repo_root / "tools/build_style_experiment_execution_plan.py"), str(packet), str(readiness), "--output", str(plan)],
            "required_output": plan,
        },
        {
            "transition_id": "build_evidence_bundle",
            "command": [py, str(repo_root / "tools/build_style_experiment_evidence_bundle.py"), str(experiment_root), "--output", manifest.name],
            "required_output": manifest,
        },
        {
            "transition_id": "verify_evidence_bundle",
            "command": [py, str(repo_root / "tools/verify_style_experiment_evidence_bundle.py"), str(experiment_root)],
            "required_output": None,
        },
    ]


def activate(
    repo_root: Path,
    experiment_root: Path,
    runner: CommandRunner = default_runner,
    env: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    journal: dict[str, Any] = {
        "schema": "stegverse.style-experiment-activation-journal.v1",
        "started_at": utc_now(),
        "completed_at": None,
        "experiment_root": str(experiment_root.resolve()),
        "status": "RUNNING",
        "execution_admissible": False,
        "publication_admissible": False,
        "transitions": [],
        "errors": errors,
    }

    packet_path = experiment_root / "packet.json"
    if not packet_path.is_file():
        errors.append("packet.json is required before activation")
    if not repo_root.is_dir():
        errors.append("repository root does not exist")
    if errors:
        journal["status"] = "BLOCKED"
        journal["completed_at"] = utc_now()
        return journal, errors

    execution_env = dict(os.environ)
    if env:
        execution_env.update(env)

    for spec in command_specs(repo_root, experiment_root):
        transition = {
            "transition_id": spec["transition_id"],
            "started_at": utc_now(),
            "completed_at": None,
            "status": "RUNNING",
            "returncode": None,
            "command": spec["command"],
            "stdout": "",
            "stderr": "",
        }
        journal["transitions"].append(transition)
        result = runner(spec["command"], repo_root, execution_env)
        transition["returncode"] = result.returncode
        transition["stdout"] = result.stdout
        transition["stderr"] = result.stderr
        transition["completed_at"] = utc_now()

        required_output = spec["required_output"]
        output_missing = required_output is not None and not Path(required_output).is_file()
        if result.returncode != 0 or output_missing:
            transition["status"] = "FAIL_CLOSED"
            if result.returncode != 0:
                errors.append(f"{spec['transition_id']} returned {result.returncode}")
            if output_missing:
                errors.append(f"{spec['transition_id']} did not create {required_output}")
            journal["status"] = "BLOCKED"
            journal["completed_at"] = utc_now()
            return journal, errors
        transition["status"] = "PASS"

    readiness = json.loads((experiment_root / "readiness-report.json").read_text(encoding="utf-8"))
    plan = json.loads((experiment_root / "execution-plan.json").read_text(encoding="utf-8"))
    manifest = json.loads((experiment_root / "manifest.json").read_text(encoding="utf-8"))
    journal["execution_admissible"] = bool(
        readiness.get("execution_admissible") is True
        and plan.get("execution_admissible") is True
        and manifest.get("verification_admissible") is True
    )
    journal["publication_admissible"] = bool(
        readiness.get("publication_admissible") is True
        and plan.get("publication_admissible") is True
        and manifest.get("publication_admissible") is True
    )
    journal["status"] = "COMPLETE" if journal["execution_admissible"] else "BLOCKED"
    if not journal["execution_admissible"]:
        errors.append("completed transitions did not establish execution admissibility")
    journal["completed_at"] = utc_now()
    return journal, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_root")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--journal", default="activation-journal.json")
    args = parser.parse_args()

    experiment_root = Path(args.experiment_root).resolve()
    repo_root = Path(args.repo_root).resolve()
    experiment_root.mkdir(parents=True, exist_ok=True)
    journal, errors = activate(repo_root, experiment_root)
    journal_path = (experiment_root / args.journal).resolve()
    try:
        journal_path.relative_to(experiment_root)
    except ValueError as exc:
        raise SystemExit("journal path escapes experiment root") from exc
    write_json(journal_path, journal)
    print(json.dumps(journal, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
