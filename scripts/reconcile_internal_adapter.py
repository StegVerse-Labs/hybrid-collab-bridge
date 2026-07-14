#!/usr/bin/env python3
"""Autonomously reconcile the internal adapter runtime to declared contracts.

This script is idempotent. It applies only bounded repository-local wiring,
compiles the API, and writes machine-readable reconciliation state. It never
executes provider output, publishes, delegates, or issues final receipts.
"""
from __future__ import annotations

import json
import py_compile
import subprocess
from datetime import datetime, timezone
from pathlib import Path

MAIN = Path("api/app/main.py")
STATE = Path("state/internal_adapter_reconciliation.json")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def install_run_boundary_if_needed() -> bool:
    text = MAIN.read_text(encoding="utf-8")
    marker = "from .governance.run_boundary import build_integrity_ledger_payload, decide_run_boundary"
    if marker in text:
        return False
    subprocess.run(
        ["python", "scripts/install_run_boundary_cge_event.py"],
        check=True,
    )
    return True


def install_repair_candidate_trace_if_needed() -> bool:
    text = MAIN.read_text(encoding="utf-8")
    import_marker = "from .governance.repair_candidate import create_repair_candidate"
    if import_marker in text:
        return False

    old_import = (
        "from .governance.run_boundary import build_integrity_ledger_payload, decide_run_boundary\n"
    )
    new_import = old_import + import_marker + "\n"
    text = replace_once(text, old_import, new_import, "repair-candidate import")

    old_boundary = '''    boundary = decide_run_boundary(
        provider_status=result["status"],
        provider_decision=final_admission.decision,
        integrity=integrity_result,
        human_gate=req.human_gate,
    )

    # Integrity evaluation is its own bounded CGE event. This receipt is
'''
    new_boundary = '''    boundary = decide_run_boundary(
        provider_status=result["status"],
        provider_decision=final_admission.decision,
        integrity=integrity_result,
        human_gate=req.human_gate,
    )

    # Repair is declared automatically when integrity fails, but never executed.
    repair_candidate = None
    repair_event_receipt = None
    if integrity_result is not None and boundary.status in {"NEEDS_REPAIR", "INTEGRITY_FAILED"}:
        repair_candidate = create_repair_candidate(
            run_id=result.get("chain_id") or str(session_dir),
            artifact_id=(req.artifact_manifest.artifact_id if req.artifact_manifest else None),
            integrity=integrity_result,
        )
        repair_event_receipt = await CGE.append_ledger(
            mutation_class="observe",
            actor=BRIDGE_ENTITY,
            payload={
                "type": "artifact_repair_candidate_declared",
                **repair_candidate.to_dict(),
                "execution_authority": False,
                "downstream_admissibility": "PENDING",
            },
            bcat={
                "observability": 1.0,
                "context_stability": 1.0,
                "authority_clarity": 1.0,
                "trust_continuity": 1.0,
                "reversibility_margin": 1.0,
                "risk": 0.0,
            },
            gcat={"g": 0.25, "c": 0.25, "a": 0.25, "t": 0.25},
        )

    # Integrity evaluation is its own bounded CGE event. This receipt is
'''
    text = replace_once(text, old_boundary, new_boundary, "repair-candidate declaration")

    old_trace = '''            "run_boundary": boundary.to_dict(),
            "integrity_event_receipt": integrity_event_receipt,
            "receipt": receipt_for_ingest,
'''
    new_trace = '''            "run_boundary": boundary.to_dict(),
            "integrity_event_receipt": integrity_event_receipt,
            "repair_candidate": repair_candidate.to_dict() if repair_candidate else None,
            "repair_event_receipt": repair_event_receipt,
            "receipt": receipt_for_ingest,
'''
    text = replace_once(text, old_trace, new_trace, "repair-candidate trace")

    MAIN.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    changes = []
    if install_run_boundary_if_needed():
        changes.append("run_boundary_cge_event")
    if install_repair_candidate_trace_if_needed():
        changes.append("repair_candidate_trace")

    py_compile.compile(str(MAIN), doraise=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": "1.0",
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "runtime": "internal_llm_adapter",
        "changes_applied": changes,
        "run_boundary_installed": True,
        "dedicated_integrity_event_installed": True,
        "repair_candidate_declaration_installed": True,
        "repair_execution_authority": False,
        "publication_authority": False,
        "delegation_authority": False,
        "final_receipt_authority": False,
        "manual_action_required": False,
    }
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(state, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
