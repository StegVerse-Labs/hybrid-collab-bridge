#!/usr/bin/env python3
"""Install artifact-integrity enforcement into the internal bridge run path.

This bounded installer performs exact-anchor replacements only. It does not
change provider behavior, BCAT/GCAT authority, publication, delegation, or
final-receipt authority.
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

    old_models_import = '''from .models import (
    RunRequest, ContinueRequest, RunResponse, Turn, ReceiptRef,
    DiscoveryRequest, DiscoveryResponse, DiscoveryResultItem, ProviderConnectRequest,
)
'''
    new_models_import = '''from .models import (
    RunRequest, ContinueRequest, RunResponse, Turn, ReceiptRef, IntegrityEvidence,
    DiscoveryRequest, DiscoveryResponse, DiscoveryResultItem, ProviderConnectRequest,
)
from .governance.artifact_integrity import evaluate_artifact_integrity
'''
    text = replace_once(text, old_models_import, new_models_import, "models import")

    old_run_block = '''    final_text = ""
    if final_admission.decision == "allow":
        final_text = final_admission.receipt.get("payload", {}).get("merge_output", {}).get("text", "")

    # Ingest to StegDB
    if final_admission.receipt:
        asyncio.create_task(STEGDB.ingest_receipt(
            receipt=final_admission.receipt,
            actor=BRIDGE_ENTITY,
            source="hybrid-collab-bridge/run",
        ))

    if req.trace_level == "full":
        final_trace = {
            "type": "consensus_merge",
            "admission": {
                "decision": final_admission.decision,
                "bcat": final_admission.bcat,
                "gcat": final_admission.gcat,
                "reasoning": final_admission.reasoning,
            },
            "receipt": final_admission.receipt,
            "chain_id": result.get("chain_id"),
        }
        write_text(session_dir, "03_referee.json", json.dumps(final_trace, indent=2))
    else:
        write_text(session_dir, "03_referee.md", final_text)

    status = "OK"
    requires_human = False
    if result["status"] == "DENIED":
        status = "DENIED"
    elif result["status"] == "DEFERRED":
        status = "PAUSED_FOR_REVIEW"
        requires_human = True
    elif req.human_gate:
        status = "PAUSED_FOR_REVIEW"
        requires_human = True
'''

    new_run_block = '''    final_text = ""
    if final_admission.decision == "allow":
        final_text = final_admission.receipt.get("payload", {}).get("merge_output", {}).get("text", "")

    # Artifact integrity is evaluated after provider admission but before
    # candidate ingestion. It does not replace BCAT/GCAT admissibility.
    integrity_result = None
    integrity_evidence = None
    if final_admission.decision == "allow":
        required_sections = (
            req.artifact_manifest.required_sections
            if req.artifact_manifest is not None
            else []
        )
        integrity_result = evaluate_artifact_integrity(final_text, required_sections)
        integrity_evidence = IntegrityEvidence(**integrity_result.to_dict())

    # Attach bounded integrity evidence to a copied receipt. A candidate with
    # failed integrity cannot enter StegDB as an accepted run result.
    receipt_for_ingest = final_admission.receipt
    if final_admission.receipt and integrity_result is not None:
        receipt_for_ingest = json.loads(json.dumps(final_admission.receipt))
        receipt_for_ingest.setdefault("payload", {})["artifact_integrity"] = integrity_result.to_dict()

    may_ingest = bool(final_admission.receipt) and (
        final_admission.decision != "allow"
        or (integrity_result is not None and integrity_result.passed)
    )
    if may_ingest:
        asyncio.create_task(STEGDB.ingest_receipt(
            receipt=receipt_for_ingest,
            actor=BRIDGE_ENTITY,
            source="hybrid-collab-bridge/run",
        ))

    if req.trace_level == "full":
        final_trace = {
            "type": "consensus_merge",
            "admission": {
                "decision": final_admission.decision,
                "bcat": final_admission.bcat,
                "gcat": final_admission.gcat,
                "reasoning": final_admission.reasoning,
            },
            "integrity": integrity_result.to_dict() if integrity_result else None,
            "receipt": receipt_for_ingest,
            "chain_id": result.get("chain_id"),
        }
        write_text(session_dir, "03_referee.json", json.dumps(final_trace, indent=2))
    else:
        write_text(session_dir, "03_referee.md", final_text)

    status = "OK"
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
    text = replace_once(text, old_run_block, new_run_block, "governed run block")

    old_response_fields = '''            final_bcat=final_admission.bcat,
            final_gcat=final_admission.gcat,
            chain_id=result.get("chain_id"),
'''
    new_response_fields = '''            final_bcat=final_admission.bcat,
            final_gcat=final_admission.gcat,
            integrity=integrity_evidence,
            chain_id=result.get("chain_id"),
'''
    text = replace_once(text, old_response_fields, new_response_fields, "response integrity field")

    MAIN.write_text(text, encoding="utf-8")
    py_compile.compile(str(MAIN), doraise=True)
    print("Installed internal artifact-integrity wiring in api/app/main.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
