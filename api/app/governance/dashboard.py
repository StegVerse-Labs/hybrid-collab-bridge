"""Governance Dashboard — Read-only operational visibility.

Endpoints for monitoring ledger state, receipt chains, entity registry,
and admission statistics. No mutations — read-only.
"""
from __future__ import annotations
from typing import Dict, Any, List
from fastapi import APIRouter, Header, HTTPException

from ..governance.entity import EntityRegistry
from ..governance.cge_client import CGELightClient

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


def auth_or_403(token: str | None, admin_token: str):
    if not admin_token:
        return
    if token != admin_token:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/ledger")
async def ledger_state(
    limit: int = 100,
    x_admin_token: str | None = Header(default=None),
):
    """Read ledger entries."""
    from ...main import ADMIN_TOKEN, CGE
    auth_or_403(x_admin_token, ADMIN_TOKEN)

    ledger_path = CGE.cge_path / "state" / "ledger.jsonl"
    if not ledger_path.exists():
        return {"entries": [], "count": 0}

    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    entries = [json.loads(line) for line in lines[-limit:]]

    return {
        "entries": entries,
        "count": len(entries),
        "total": len(lines),
    }


@router.get("/receipts/{receipt_id}")
async def receipt_detail(
    receipt_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Get receipt details and verification status."""
    from ...main import ADMIN_TOKEN, CGE
    auth_or_403(x_admin_token, ADMIN_TOKEN)

    import json
    receipt_path = CGE.cge_path / "meta" / "receipts" / "latest_receipt.json"
    if not receipt_path.exists():
        raise HTTPException(404, "No receipts found")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    # If querying a specific receipt, search ledger
    ledger_path = CGE.cge_path / "state" / "ledger.jsonl"
    if ledger_path.exists():
        lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
        for line in lines:
            entry = json.loads(line)
            # Check if this entry's receipt matches
            if entry.get("receipt_id") == receipt_id:
                return {
                    "receipt": receipt,
                    "ledger_entry": entry,
                    "verified": True,
                }

    return {
        "receipt": receipt,
        "verified": receipt.get("receipt_id") == receipt_id,
    }


@router.get("/entities")
async def entity_registry(
    x_admin_token: str | None = Header(default=None),
):
    """List all governed entities."""
    from ...main import ADMIN_TOKEN, ENTITY_REG
    auth_or_403(x_admin_token, ADMIN_TOKEN)

    entities = [e.to_dict() for e in ENTITY_REG.all()]
    return {
        "entities": entities,
        "count": len(entities),
        "org_id": ENTITY_REG.org_id,
    }


@router.get("/stats")
async def admission_stats(
    x_admin_token: str | None = Header(default=None),
):
    """Admission statistics."""
    from ...main import ADMIN_TOKEN, CGE
    auth_or_403(x_admin_token, ADMIN_TOKEN)

    ledger_path = CGE.cge_path / "state" / "ledger.jsonl"
    if not ledger_path.exists():
        return {"total": 0, "approved": 0, "rejected": 0, "compensation": 0}

    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    approved = rejected = compensation = 0

    for line in lines:
        entry = json.loads(line)
        mutation = entry.get("mutation_class", "")
        if mutation == "approve":
            approved += 1
        elif mutation == "reject":
            rejected += 1
        elif mutation == "compensation":
            compensation += 1

    return {
        "total": len(lines),
        "approved": approved,
        "rejected": rejected,
        "compensation": compensation,
        "approval_rate": approved / max(len(lines), 1),
    }


@router.get("/receipt-chain/{chain_id}")
async def receipt_chain(
    chain_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Get receipt chain by ID."""
    from ...main import ADMIN_TOKEN, CGE
    auth_or_403(x_admin_token, ADMIN_TOKEN)

    chain_path = CGE.cge_path / "meta" / "receipt_chains.jsonl"
    if not chain_path.exists():
        raise HTTPException(404, "No chains found")

    import json
    lines = chain_path.read_text(encoding="utf-8").strip().splitlines()
    chain_entries = []

    for line in lines:
        entry = json.loads(line)
        if entry.get("chain_id") == chain_id or entry.get("previous_receipt_id") == chain_id:
            chain_entries.append(entry)

    return {
        "chain_id": chain_id,
        "entries": chain_entries,
        "length": len(chain_entries),
    }
