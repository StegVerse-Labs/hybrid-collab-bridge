"""Governance Dashboard — operational visibility and governed sub-routers.

Dashboard endpoints are read-only. Mutation-capable governance surfaces are
mounted as explicit subordinate routers and retain their own admission logic.
"""
from __future__ import annotations
import builtins
import json
import os
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException

from .human_llm_interoperability import (
    router as interoperability_router,
    configure as configure_interoperability,
)

# main.py currently configures the dashboard before assigning its module-level
# ADMIN_TOKEN. Python falls back to builtins for the first lookup; establish the
# environment-derived value here so application import remains deterministic.
if not hasattr(builtins, "ADMIN_TOKEN"):
    builtins.ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])

ADMIN_TOKEN: str = ""
CGE_PATH: Path = Path("./cge_light")
ENTITY_REGISTRY = None


def set_config(admin_token: str, cge_path: Path, entity_registry):
    """Set dashboard and subordinate governance-router config from main.py."""
    global ADMIN_TOKEN, CGE_PATH, ENTITY_REGISTRY
    ADMIN_TOKEN = admin_token
    CGE_PATH = cge_path
    ENTITY_REGISTRY = entity_registry
    configure_interoperability(admin_token=admin_token, cge_path=cge_path)


def auth_or_403(token: str | None):
    if not ADMIN_TOKEN:
        return
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/ledger")
async def ledger_state(limit: int = 100, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
    if not ledger_path.exists():
        return {"entries": [], "count": 0}
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    entries = [json.loads(line) for line in lines[-limit:]]
    return {"entries": entries, "count": len(entries), "total": len(lines)}


@router.get("/receipts/{receipt_id}")
async def receipt_detail(receipt_id: str, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    receipt_path = CGE_PATH / "meta" / "receipts" / "latest_receipt.json"
    if not receipt_path.exists():
        raise HTTPException(404, "No receipts found")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").strip().splitlines():
            entry = json.loads(line)
            if entry.get("receipt_id") == receipt_id:
                return {"receipt": receipt, "ledger_entry": entry, "verified": True}
    return {"receipt": receipt, "verified": receipt.get("receipt_id") == receipt_id}


@router.get("/entities")
async def entity_registry(x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    if ENTITY_REGISTRY is None:
        return {"entities": [], "count": 0, "org_id": "unknown"}
    entities = [e.to_dict() for e in ENTITY_REGISTRY.all()]
    return {"entities": entities, "count": len(entities), "org_id": ENTITY_REGISTRY.org_id}


@router.get("/stats")
async def admission_stats(x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
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
async def receipt_chain(chain_id: str, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    chain_path = CGE_PATH / "meta" / "receipt_chains.jsonl"
    if not chain_path.exists():
        raise HTTPException(404, "No chains found")
    chain_entries = []
    for line in chain_path.read_text(encoding="utf-8").strip().splitlines():
        entry = json.loads(line)
        if entry.get("chain_id") == chain_id or entry.get("previous_receipt_id") == chain_id:
            chain_entries.append(entry)
    return {"chain_id": chain_id, "entries": chain_entries, "length": len(chain_entries)}


# main.py already registers this router. The subordinate assessment routes are
# therefore available under /v1/dashboard/v1/interoperability/* until the
# planned main-router cleanup moves them to /v1/interoperability/* directly.
router.include_router(interoperability_router)
