"""Governed Hybrid Collab Bridge API.

Every endpoint is admission-gated. Human gate is exception-only.
"""
import os
import json
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from .models import RunRequest, ContinueRequest, RunResponse, Turn, ReceiptRef
from .registry import ProviderRegistry
from .strategies import governed_consensus
from .session_writer import ensure_session, write_text
from .governance.entity import EntityIdentity, EntityRegistry
from .governance.cge_client import CGELightClient
from .governance.admission import AdmissionGate

# -- Configuration -----------------------------------------------

DEFAULT_CFG = (Path(__file__).resolve().parents[2] / "providers.yaml").resolve()
env_cfg = os.getenv("HCB_PROVIDERS_PATH")
if env_cfg:
    cfg_path = Path(env_cfg)
    if not cfg_path.is_absolute():
        workspace = Path(os.getenv("GITHUB_WORKSPACE", DEFAULT_CFG.parents[1]))
        cfg_path = (workspace / env_cfg).resolve()
else:
    cfg_path = DEFAULT_CFG

REG = ProviderRegistry(cfg_path=str(cfg_path))

ORG_ID = os.getenv("HCB_ORG_ID", "StegVerse-Labs")
CGE_MODE = os.getenv("HCB_CGE_MODE", "embedded")
CGE_ENDPOINT = os.getenv("HCB_CGE_ENDPOINT", None)
CGE_PATH = os.getenv("HCB_CGE_PATH", None)

CGE = CGELightClient(
    org_id=ORG_ID,
    mode=CGE_MODE,
    endpoint=CGE_ENDPOINT,
    cge_path=CGE_PATH,
)

import yaml
constitution_path = Path(CGE.cge_path / "repo_constitution.yml")
constitution = yaml.safe_load(constitution_path.read_text()) if constitution_path.exists() else {}
GATE = AdmissionGate(cge_client=CGE, constitution=constitution)

ENTITY_REG = EntityRegistry(org_id=ORG_ID)

BRIDGE_ENTITY = EntityIdentity(
    entity_id=f"bridge-{ORG_ID.lower().replace(" ", "-")}",
    entity_type="automated_process",
    org_id=ORG_ID,
    owner_human=os.getenv("HCB_OWNER_HUMAN", "owner"),
    owner_ai=os.getenv("HCB_OWNER_AI", "Beta_Orionis"),
    capability_set=["orchestration", "consensus", "governance"],
    governance_scope="internal",
)
ENTITY_REG.register(BRIDGE_ENTITY)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

app = FastAPI(title="Hybrid Collab Bridge (Governed)", version="0.2.0")

# -- Auth --------------------------------------------------------

def auth_or_403(token: str | None):
    if not ADMIN_TOKEN:
        return
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: bad admin token")

# -- Health ------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "ok": True,
        "version": "0.2.0",
        "providers": REG.list(),
        "providers_path": str(cfg_path),
        "org_id": ORG_ID,
        "cge_mode": CGE_MODE,
        "cge_path": str(CGE.cge_path),
        "bridge_entity": BRIDGE_ENTITY.to_dict(),
    }

# -- Run (governed) ----------------------------------------------

@app.post("/v1/run", response_model=RunResponse)
async def run_collab(req: RunRequest, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)

    caller_entity = BRIDGE_ENTITY
    if req.entity_id:
        caller = ENTITY_REG.get(req.entity_id)
        if caller:
            caller_entity = caller

    session_dir = ensure_session(req.slug)

    text_prompt = f"{req.question}\n\nContext:\n{req.context or ''}\n\nConstraints:\n- Tone: concise\n"
    opts = {"temperature": req.temperature}

    result = await governed_consensus(
        reg=REG,
        gate=GATE,
        experts=req.experts,
        prompt=text_prompt,
        opts=opts,
        bridge_entity=caller_entity,
    )

    turns = []
    idx = 1
    for p in result["proposals"]:
        admission = p["admission"]
        turn = Turn(
            who=p["who"],
            output=p["out"].get("text", ""),
            receipt=ReceiptRef(
                receipt_id=admission.receipt.get("receipt_id", ""),
                ledger_entry_id=admission.receipt.get("ledger_entry_id", ""),
                entry_hash=admission.receipt.get("entry_hash", ""),
                decision=admission.decision,
                verified=admission.receipt.get("verified", False),
            ) if admission.receipt else None,
            bcat=admission.bcat,
            gcat=admission.gcat,
            decision=admission.decision,
        )
        turns.append(turn)

        if req.trace_level == "full":
            trace = {
                "turn": idx,
                "expert": p["who"],
                "output": p["out"].get("text", ""),
                "admission": {
                    "decision": admission.decision,
                    "bcat": admission.bcat,
                    "gcat": admission.gcat,
                    "reasoning": admission.reasoning,
                },
                "receipt": admission.receipt,
            }
            write_text(session_dir, f"{idx:02d}_{p['who']}.json", json.dumps(trace, indent=2))
        else:
            write_text(session_dir, f"{idx:02d}_{p['who']}.md", p["out"].get("text", ""))
        idx += 1

    final_admission = result["final"]
    final_text = ""
    if final_admission.decision == "allow":
        final_text = final_admission.receipt.get("payload", {}).get("merge_output", {}).get("text", "")

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

    return JSONResponse(
        RunResponse(
            status=status,
            session_path=str(session_dir),
            strategy=req.strategy,
            turns=turns,
            final=final_text,
            final_receipt=ReceiptRef(
                receipt_id=final_admission.receipt.get("receipt_id", ""),
                ledger_entry_id=final_admission.receipt.get("ledger_entry_id", ""),
                entry_hash=final_admission.receipt.get("entry_hash", ""),
                decision=final_admission.decision,
                verified=final_admission.receipt.get("verified", False),
            ) if final_admission.receipt else None,
            final_bcat=final_admission.bcat,
            final_gcat=final_admission.gcat,
            chain_id=result.get("chain_id"),
            requires_human=requires_human,
            reasoning=final_admission.reasoning,
        ).model_dump()
    )

# -- Continue (quorum approval) --------------------------------

@app.post("/v1/continue", response_model=RunResponse)
async def continue_collab(req: ContinueRequest, x_admin_token: str | None = Header(default=None)):
    auth_or_403(x_admin_token)

    p = Path(req.session_path)
    if not p.exists():
        raise HTTPException(404, "Session path not found")

    ref_file = p / "03_referee.json"
    if not ref_file.exists():
        ref_file = p / "03_referee.md"

    final_text = ""
    if ref_file.exists():
        if ref_file.suffix == ".json":
            trace = json.loads(ref_file.read_text(encoding="utf-8"))
            final_text = trace.get("receipt", {}).get("payload", {}).get("merge_output", {}).get("text", "")
        else:
            final_text = ref_file.read_text(encoding="utf-8").strip()

    approver = ENTITY_REG.get(req.approver_entity_id)
    if not approver:
        approver = EntityIdentity(
            entity_id=req.approver_entity_id,
            entity_type=req.approver_type,
            org_id=ORG_ID,
            owner_human=BRIDGE_ENTITY.owner_human,
        )

    # Quorum enforcement for policy-level approvals
    if req.approval == "quorum_approve":
        constitution = GATE.constitution
        quorum_rules = constitution.get("quorum_rules", {})
        policy_rule = quorum_rules.get("policy_change", {})
        required_types = policy_rule.get("required", [])
        if req.approver_type not in required_types:
            raise HTTPException(403, f"Approver type {req.approver_type} not authorized for quorum")

    approval_receipt = await CGE.append_ledger(
        mutation_class="approve",
        actor=approver,
        payload={
            "type": "continuation_approval",
            "session_path": str(p),
            "approval_type": req.approval,
            "notes": req.notes,
            "previous_status": "DEFERRED",
        },
        bcat={"observability": 1.0, "context_stability": 1.0, "authority_clarity": 1.0,
              "trust_continuity": 1.0, "reversibility_margin": 0.5, "risk": 0.1},
        gcat={"g": 0.25, "c": 0.25, "a": 0.25, "t": 0.25},
    )

    return JSONResponse(
        RunResponse(
            status="OK",
            session_path=str(p),
            strategy="consensus",
            turns=[],
            final=final_text,
            final_receipt=ReceiptRef(
                receipt_id=approval_receipt.get("receipt_id", ""),
                ledger_entry_id=approval_receipt.get("ledger_entry_id", ""),
                entry_hash=approval_receipt.get("entry_hash", ""),
                decision="allow",
                verified=approval_receipt.get("verified", False),
            ),
            requires_human=False,
            reasoning=f"Approved by {req.approver_type}: {req.approver_entity_id}",
        ).model_dump()
    )
