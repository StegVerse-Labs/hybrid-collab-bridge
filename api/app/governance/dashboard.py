"""Governance dashboard and governed interoperability routers."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from .human_llm_interoperability import configure as configure_interoperability
from .human_llm_interoperability import router as interoperability_router
from .human_llm_replay import configure_replay
from .human_llm_replay import router as interoperability_replay_router

router = APIRouter()
ADMIN_TOKEN: str = ""
CGE_PATH: Path = Path("./cge_light")
ENTITY_REGISTRY = None


def set_config(admin_token: str, cge_path: Path, entity_registry):
    global ADMIN_TOKEN, CGE_PATH, ENTITY_REGISTRY
    ADMIN_TOKEN = admin_token
    CGE_PATH = Path(cge_path)
    ENTITY_REGISTRY = entity_registry
    configure_interoperability(admin_token=admin_token, cge_path=CGE_PATH)
    configure_replay(admin_token=admin_token)


def auth_or_403(token: str | None):
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/v1/dashboard/ledger", tags=["dashboard"])
async def ledger_state(limit: int = 100, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
    if not ledger_path.exists():
        return {"entries": [], "count": 0}
    lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines[-limit:]]
    return {"entries": entries, "count": len(entries), "total": len(lines)}


@router.get("/v1/dashboard/receipts/{receipt_id}", tags=["dashboard"])
async def receipt_detail(receipt_id: str, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    receipt_path = CGE_PATH / "meta" / "receipts" / "latest_receipt.json"
    if not receipt_path.exists():
        raise HTTPException(404, "No receipts found")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("receipt_id") == receipt_id:
                return {"receipt": receipt, "ledger_entry": entry, "verified": True}
    return {"receipt": receipt, "verified": receipt.get("receipt_id") == receipt_id}


@router.get("/v1/dashboard/entities", tags=["dashboard"])
async def entity_registry(x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    if ENTITY_REGISTRY is None:
        return {"entities": [], "count": 0, "org_id": "unknown"}
    entities = [entity.to_dict() for entity in ENTITY_REGISTRY.all()]
    return {"entities": entities, "count": len(entities), "org_id": ENTITY_REGISTRY.org_id}


@router.get("/v1/dashboard/stats", tags=["dashboard"])
async def admission_stats(x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    ledger_path = CGE_PATH / "state" / "ledger.jsonl"
    if not ledger_path.exists():
        return {"total": 0, "approved": 0, "rejected": 0, "compensation": 0}
    lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    approved = rejected = compensation = 0
    for line in lines:
        mutation = json.loads(line).get("mutation_class", "")
        approved += mutation == "approve"
        rejected += mutation == "reject"
        compensation += mutation == "compensation"
    return {
        "total": len(lines),
        "approved": approved,
        "rejected": rejected,
        "compensation": compensation,
        "approval_rate": approved / max(len(lines), 1),
    }


@router.get("/v1/dashboard/receipt-chain/{chain_id}", tags=["dashboard"])
async def receipt_chain(chain_id: str, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)
    chain_path = CGE_PATH / "meta" / "receipt_chains.jsonl"
    if not chain_path.exists():
        raise HTTPException(404, "No chains found")
    entries = []
    for line in chain_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if chain_id in {entry.get("chain_id"), entry.get("previous_receipt_id")}:
            entries.append(entry)
    return {"chain_id": chain_id, "entries": entries, "length": len(entries)}


router.include_router(interoperability_router)
router.include_router(interoperability_replay_router)
