#!/usr/bin/env python3
"""Install run-boundary policy and dedicated CGE integrity events.

Exact-anchor mutation only. This installer does not grant execution,
publication, delegation, or final-receipt authority.
"""
from pathlib import Path
import py_compile

MAIN = Path("api/app/main.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = MAIN.read_text(encoding="utf-8")

    old_import = "from .governance.artifact_integrity import evaluate_artifact_integrity\n"
    new_import = (
        "from .governance.artifact_integrity import evaluate_artifact_integrity\n"
        "from .governance.run_boundary import build_integrity_ledger_payload, decide_run_boundary\n"
    )
    text = replace_once(text, old_import, new_import, "run-boundary import")

    old_boundary = '''    may_ingest = bool(final_admission.receipt) and (
        final_admission.decision != "allow"
        or (integrity_result is not None and integrity_result.passed)
    )
    if may_ingest:
        asyncio.create_task(STEGDB.ingest_receipt(
            receipt=receipt_for_ingest,
            actor=BRIDGE_ENTITY,
            source="hybrid-collab-bridge/run",
        ))
'''
    new_boundary = '''    boundary = decide_run_boundary(
        provider_status=result["status"],
        provider_decision=final_admission.decision,
        integrity=integrity_result,
        human_gate=req.human_gate,
    )

    # Integrity evaluation is its own bounded CGE event. This receipt is
    # monitoring evidence only and does not become a final receipt.
    integrity_event_receipt = None
    if integrity_result is not None:
        integrity_payload = build_integrity_ledger_payload(
            run_id=result.get("chain_id"),
            artifact_id=(req.artifact_manifest.artifact_id if req.artifact_manifest else None),
            integrity=integrity_result,
            boundary=boundary,
        )
        integrity_event_receipt = await CGE.append_ledger(
            mutation_class="observe",
            actor=BRIDGE_ENTITY,
            payload=integrity_payload,
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

    if boundary.may_ingest_accepted_result:
        asyncio.create_task(STEGDB.ingest_receipt(
            receipt=receipt_for_ingest,
            actor=BRIDGE_ENTITY,
            source="hybrid-collab-bridge/run",
        ))
'''
    text = replace_once(text, old_boundary, new_boundary, "accepted-result boundary")

    old_trace = '''            "integrity": integrity_result.to_dict() if integrity_result else None,
            "receipt": receipt_for_ingest,
            "chain_id": result.get("chain_id"),
'''
    new_trace = '''            "integrity": integrity_result.to_dict() if integrity_result else None,
            "run_boundary": boundary.to_dict(),
            "integrity_event_receipt": integrity_event_receipt,
            "receipt": receipt_for_ingest,
            "chain_id": result.get("chain_id"),
'''
    text = replace_once(text, old_trace, new_trace, "trace evidence")

    old_status = '''    status = "OK"
    requires_human = False
    if result["status"] == "DENIED":
        status = "ADMISSIBILITY_FAILED"
    elif result["status"] == "DEFERRED":
        status = "EXCEPTION_REVIEW"
        requires_human = True
    elif integrity_result and integrity_result.decision == "FAIL_CLOSED":
        status = "INTEGRITY_FAILED"
    elif integrity_result and integrity_result.decision == "NEEDS_REPAIR":
        status = "NEEDS_REPAIR"
    elif req.human_gate:
        status = "EXCEPTION_REVIEW"
        requires_human = True
'''
    new_status = '''    status = boundary.status
    requires_human = boundary.requires_human
'''
    text = replace_once(text, old_status, new_status, "status policy")

    old_reasoning = '''            requires_human=requires_human,
            reasoning=final_admission.reasoning,
'''
    new_reasoning = '''            requires_human=requires_human,
            reasoning=boundary.reasoning,
'''
    text = replace_once(text, old_reasoning, new_reasoning, "boundary reasoning")

    MAIN.write_text(text, encoding="utf-8")
    py_compile.compile(str(MAIN), doraise=True)
    print("Installed deterministic run-boundary policy and CGE integrity event")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
