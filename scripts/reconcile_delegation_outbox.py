#!/usr/bin/env python3
"""Build bounded delegation candidates from governed session traces.

The reconciler scans completed session traces, emits deterministic outbox records,
and writes queue state. It never transmits, delegates, executes, publishes, or
issues final receipts.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from api.app.governance.delegation_candidate import build_delegation_candidate


def _receipt_ref(receipt: Any) -> str | None:
    if not isinstance(receipt, dict):
        return None
    value = receipt.get("receipt_id") or receipt.get("ledger_entry_id") or receipt.get("entry_hash")
    return str(value).strip() if value else None


def _identity(trace: dict[str, Any], source: Path) -> tuple[str, str, str, str]:
    receipt = trace.get("receipt") if isinstance(trace.get("receipt"), dict) else {}
    payload = receipt.get("payload") if isinstance(receipt.get("payload"), dict) else {}
    transition_id = str(
        trace.get("transition_id")
        or payload.get("transition_id")
        or receipt.get("transition_id")
        or source.parent.name
    )
    run_id = str(trace.get("chain_id") or payload.get("run_id") or receipt.get("run_id") or source.parent.name)
    event_id = str(payload.get("event_id") or receipt.get("ledger_entry_id") or receipt.get("receipt_id") or source.stem)
    origin_manifest_id = str(
        payload.get("origin_manifest_id")
        or receipt.get("origin_manifest_id")
        or f"session:{source.parent.as_posix()}"
    )
    return transition_id, run_id, event_id, origin_manifest_id


def candidate_from_trace(trace: dict[str, Any], source: Path):
    integrity = trace.get("integrity") if isinstance(trace.get("integrity"), dict) else {}
    boundary = trace.get("run_boundary") if isinstance(trace.get("run_boundary"), dict) else {}
    transition_id, run_id, event_id, origin_manifest_id = _identity(trace, source)

    evidence_refs = [
        ref
        for ref in (
            _receipt_ref(trace.get("receipt")),
            _receipt_ref(trace.get("integrity_event_receipt")),
            _receipt_ref(trace.get("repair_event_receipt")),
        )
        if ref
    ]
    repair = trace.get("repair_candidate") if isinstance(trace.get("repair_candidate"), dict) else {}
    repair_ref = repair.get("repair_candidate_id")

    return build_delegation_candidate(
        transition_id=transition_id,
        run_id=run_id,
        event_id=event_id,
        origin_manifest_id=origin_manifest_id,
        bridge_status=str(boundary.get("status") or "INTEGRITY_FAILED"),
        content_sha256=str(integrity.get("content_sha256") or "0" * 64),
        integrity_decision=str(integrity.get("decision") or "FAIL_CLOSED"),
        evidence_refs=evidence_refs or [f"trace:{source.as_posix()}"],
        integrity_evidence_ref=_receipt_ref(trace.get("integrity_event_receipt")),
        repair_candidate_ref=str(repair_ref) if repair_ref else None,
    )


def reconcile(sessions: Path, outbox: Path, state_path: Path) -> dict[str, Any]:
    outbox.mkdir(parents=True, exist_ok=True)
    processed: list[str] = []
    skipped: list[dict[str, str]] = []

    for source in sorted(sessions.glob("**/03_referee.json")):
        try:
            trace = json.loads(source.read_text(encoding="utf-8"))
            candidate = candidate_from_trace(trace, source)
            target = outbox / f"{candidate.candidate_id}.json"
            target.write_text(json.dumps(candidate.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            processed.append(str(target))
        except Exception as exc:  # fail one record without suppressing queue evidence
            skipped.append({"source": str(source), "error": f"{type(exc).__name__}: {exc}"})

    state = {
        "schema_version": "1.0",
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "queue": "ecosystem_delegation_outbox",
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "records": processed,
        "skipped": skipped,
        "transmission_authority": False,
        "delegation_authority": False,
        "manual_action_required": False,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=Path, default=Path("sessions"))
    parser.add_argument("--outbox", type=Path, default=Path("outbox/ecosystem-delegation"))
    parser.add_argument("--state", type=Path, default=Path("state/delegation_outbox_reconciliation.json"))
    args = parser.parse_args()
    state = reconcile(args.sessions, args.outbox, args.state)
    print(json.dumps(state, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
