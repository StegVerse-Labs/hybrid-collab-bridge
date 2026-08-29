"""Governed Hybrid Collab Bridge API.

Every endpoint is admission-gated. Human gate is exception-only.
"""
import os
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from .models import RunRequest, ContinueRequest, RunResponse, Turn, ReceiptRef
from .registry import ProviderRegistry
from .strategies import governed_consensus
from .session_writer import ensure_session, write_text
from .governance.entity import EntityIdentity, EntityRegistry
from .governance.cge_client import CGELightClient
from .governance.admission import AdmissionGate
from .governance.discovery import ProviderDiscoveryEngine, DiscoveryResult
from .governance.stegdb import StegDBClient
from .governance.compensation import CompensationTracker
from .governance.halt import EmergencyHalt
from .governance.sdk_alignment import SharedGovernanceSurface
from .governance.stegdb_wiring import StegDBWiring
from .governance.publisher import PublisherClient, PublishableOutput
from .governance.aacte_demo import AaCTEDemoPipeline
from .governance.stegcge_compiler import StegCGECompiler
from .models import (
    RunRequest, ContinueRequest, RunResponse, Turn, ReceiptRef, IntegrityEvidence,
    DiscoveryRequest, DiscoveryResponse, DiscoveryResultItem, ProviderConnectRequest,
)
from .governance.artifact_integrity import evaluate_artifact_integrity
from .governance.run_boundary import build_integrity_ledger_payload, decide_run_boundary
from .governance.repair_candidate import create_repair_candidate

# -- Configuration -----------------------------------------------

DEFAULT_CFG = (Path(__file__).resolve().parents[2] / "providers.txt").resolve()
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
ADMIN_AUTH_STATE = "TVC_ADMITTED_ADMIN_AUTH_REQUIRED"
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
constitution_path = Path(CGE.cge_path / "repo_constitution.txt")
constitution = yaml.safe_load(constitution_path.read_text()) if constitution_path.exists() else {}
GATE = AdmissionGate(cge_client=CGE, constitution=constitution)

ENTITY_REG = EntityRegistry(org_id=ORG_ID)
DISCOVERY = ProviderDiscoveryEngine()

# Configure dashboard
from .governance.dashboard import set_config as set_dashboard_config
set_dashboard_config(None, CGE.cge_path, ENTITY_REG)
STEGDB = StegDBClient(mode="direct" if os.getenv("HCB_STEGDB_ENDPOINT") else "filesystem")
COMPENSATION = CompensationTracker(cge_client=CGE)
HALT = EmergencyHalt(cge_client=CGE, constitution=constitution)
SDK_SURFACE = SharedGovernanceSurface(cge_client=CGE, constitution=constitution)
STEGDB_WIRING = StegDBWiring()
PUBLISHER = PublisherClient()
AACTE = AaCTEDemoPipeline(cge_client=CGE, constitution=constitution)
STEGCGE = StegCGECompiler()

BRIDGE_ENTITY = EntityIdentity(
    entity_id=f"bridge-{ORG_ID.lower().replace(' ', '-')}",
    entity_type="automated_process",
    org_id=ORG_ID,
    owner_human=os.getenv("HCB_OWNER_HUMAN", "owner"),
    owner_ai=os.getenv("HCB_OWNER_AI", "Beta_Orionis"),
    capability_set=["orchestration", "consensus", "governance"],
    governance_scope="internal",
)
ENTITY_REG.register(BRIDGE_ENTITY)



app = FastAPI(title="Hybrid Collab Bridge (Governed)", version="1.0.0")

# Include dashboard router
from .governance.dashboard import router as dashboard_router
app.include_router(dashboard_router)

# -- Auth --------------------------------------------------------

def auth_or_403(token: str | None):
    """Fail closed until an admitted TV/TVC admin-authorization route exists.

    The bridge must not materialize or compare an administrative bearer
    credential. Caller-supplied token text is ignored and never becomes
    authority.
    """
    del token
    raise HTTPException(
        status_code=503,
        detail=ADMIN_AUTH_STATE,
    )

# -- Health ------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "ok": True,
        "version": "1.0.0",
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

    # Emergency halt check
    if HALT.is_halted:
        raise HTTPException(503, f"Emergency halt active: {HALT.get_status()['halt_record']['reason']}")

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

    # Record compensation for all participants
    for turn in turns:
        if turn.receipt:
            # Find the entity for this turn
            entity_id = f"{BRIDGE_ENTITY.entity_id}-{turn.who}"
            entity = ENTITY_REG.get(entity_id)
            if entity:
                # Build receipt dict from the actual ledger receipt
                receipt_dict = {
                    "receipt_id": turn.receipt.receipt_id,
                    "ledger_entry_id": turn.receipt.ledger_entry_id,
                    "entry_hash": turn.receipt.entry_hash,
                    "decision": turn.receipt.decision,
                    "verified": turn.receipt.verified,
                }
                comp = COMPENSATION.calculate_compensation(entity, receipt_dict)
                asyncio.create_task(COMPENSATION.record_compensation(comp))

    final_text = ""
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

    boundary = decide_run_boundary(
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
            "run_boundary": boundary.to_dict(),
            "integrity_event_receipt": integrity_event_receipt,
            "repair_candidate": repair_candidate.to_dict() if repair_candidate else None,
            "repair_event_receipt": repair_event_receipt,
            "receipt": receipt_for_ingest,
            "chain_id": result.get("chain_id"),
        }
        write_text(session_dir, "03_referee.json", json.dumps(final_trace, indent=2))
    else:
        write_text(session_dir, "03_referee.md", final_text)

    status = boundary.status
    requires_human = boundary.requires_human

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
            integrity=integrity_evidence,
            chain_id=result.get("chain_id"),
            requires_human=requires_human,
            reasoning=boundary.reasoning,
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



# -- Emergency Halt --------------------------------------------

@app.post("/v1/halt/request")
async def request_halt(
    reason: str,
    requester_entity_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Request emergency halt. Requires quorum per constitution."""
    auth_or_403(x_admin_token)

    requester = ENTITY_REG.get(requester_entity_id)
    if not requester:
        requester = EntityIdentity(
            entity_id=requester_entity_id,
            entity_type="human_operator",  # Assume human if not registered
            org_id=ORG_ID,
            owner_human=BRIDGE_ENTITY.owner_human,
        )

    result = await HALT.request_halt(requester, reason)
    return result


@app.post("/v1/halt/lift")
async def lift_halt(
    reason: str,
    requester_entity_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Lift emergency halt. Requires same quorum as activation."""
    auth_or_403(x_admin_token)

    requester = ENTITY_REG.get(requester_entity_id)
    if not requester:
        requester = EntityIdentity(
            entity_id=requester_entity_id,
            entity_type="human_operator",
            org_id=ORG_ID,
            owner_human=BRIDGE_ENTITY.owner_human,
        )

    result = await HALT.lift_halt(requester, reason)
    return result


@app.get("/v1/halt/status")
async def halt_status(x_admin_token: str | None = Header(default=None)):
    """Get emergency halt status."""
    auth_or_403(x_admin_token)
    return HALT.get_status()

# -- Provider Discovery ------------------------------------------

@app.post("/v1/discover", response_model=DiscoveryResponse)
async def discover_providers(req: DiscoveryRequest, x_admin_token: str | None = Header(default=None)):
    """Discover available AI providers or query a specific one.

    Query types:
    - "other" or "scan" -> Full scan (local + env + network)
    - Specific name (e.g., "openai", "kimi", "ollama") -> Query that provider
    - "local" -> Scan only local servers
    - "cloud" -> Scan only cloud providers with env keys
    """
    auth_or_403(x_admin_token)

    results = []
    scan_type = req.scan_type

    if req.query.lower() in ["other", "scan", "all", "discover"]:
        # Full discovery scan
        scan_type = "auto"
        raw_results = await DISCOVERY.scan_all()
        results = [_convert_discovery(r) for r in raw_results]
    elif req.query.lower() in ["local", "on-premise", "self-hosted"]:
        scan_type = "local"
        raw_results = await DISCOVERY.scan_local()
        results = [_convert_discovery(r) for r in raw_results]
    elif req.query.lower() in ["cloud", "env", "api"]:
        scan_type = "env"
        raw_results = await DISCOVERY.scan_environment()
        results = [_convert_discovery(r) for r in raw_results]
    else:
        # Query specific provider
        scan_type = "query"
        result = DISCOVERY.query_provider(req.query)
        results = [_convert_discovery(result)]

    available = [r for r in results if r.status == "available"]
    discoverable = [r for r in results if r.status == "discoverable"]
    denied = [r for r in results if r.status == "denied"]

    return DiscoveryResponse(
        scan_type=scan_type,
        results=results,
        total_found=len(results),
        total_available=len(available),
        total_discoverable=len(discoverable),
        total_denied=len(denied),
    )


@app.get("/v1/discover/scan")
async def quick_scan(x_admin_token: str | None = Header(default=None)):
    """Quick scan — returns only available providers."""
    auth_or_403(x_admin_token)
    raw_results = await DISCOVERY.scan_all()
    available = [r for r in raw_results if r.status == "available"]
    return {
        "available": [_convert_discovery(r).model_dump() for r in available],
        "count": len(available),
    }


@app.post("/v1/discover/connect")
async def connect_provider(req: ProviderConnectRequest, x_admin_token: str | None = Header(default=None)):
    """Connect a discovered provider to the bridge."""
    auth_or_403(x_admin_token)

    # Validate the provider type exists
    from .registry import FACTORY
    if req.provider_type not in FACTORY:
        raise HTTPException(400, f"Unknown provider type: {req.provider_type}")

    # Add to providers.txt
    providers_path = Path(cfg_path)
    with providers_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Check if already exists
    existing = [p for p in cfg.get("providers", []) if p.get("name") == req.provider_id]
    if existing:
        return {"status": "already_connected", "provider": req.provider_id}

    # Add new provider entry
    new_entry = {
        "name": req.provider_id,
        "type": req.provider_type,
        "enabled": True,
        "capabilities": req.config.get("capabilities", ["text-generate"]),
    }
    cfg["providers"].append(new_entry)

    with providers_path.open("w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

    # Reload registry
    REG.reload()

    # Test connection if requested
    test_result = None
    if req.test_connection:
        provider = REG.get(req.provider_id)
        if provider:
            from .tasks import Task
            try:
                test_output = await provider.run(Task("text-generate", "Say 'connected'", {"temperature": 0.0}))
                test_result = {
                    "success": True,
                    "output": test_output.get("text", "")[:100],
                }
            except Exception as e:
                test_result = {
                    "success": False,
                    "error": str(e),
                }

    return {
        "status": "connected",
        "provider": req.provider_id,
        "type": req.provider_type,
        "test": test_result,
        "instructions": [
            f"Provider '{req.provider_id}' added to providers.txt",
            "It is now available in /v1/run requests.",
        ],
    }


def _convert_discovery(result: DiscoveryResult) -> DiscoveryResultItem:
    """Convert internal DiscoveryResult to Pydantic model."""
    return DiscoveryResultItem(
        provider_id=result.provider_id,
        provider_name=result.provider_name,
        provider_type=result.provider_type,
        status=result.status,
        reason=result.reason,
        connection_method=result.connection_method,
        instructions=result.instructions,
        config_template=result.config_template,
        requires_network=result.requires_network,
        requires_api_key=result.requires_api_key,
        estimated_cost_tier=result.estimated_cost_tier,
    )


# -- SDK Alignment -----------------------------------------------

@app.post("/v1/sdk/govern")
async def sdk_govern_output(
    provider: str,
    model: str,
    prompt: str,
    output: str,
    entity_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Govern user-facing LLM output (SDK parity endpoint)."""
    auth_or_403(x_admin_token)

    entity = ENTITY_REG.get(entity_id) or EntityIdentity(
        entity_id=entity_id,
        entity_type="ai_entity",
        org_id=ORG_ID,
        owner_human=BRIDGE_ENTITY.owner_human,
    )

    result = await SDK_SURFACE.govern_llm_output(
        provider=provider,
        model=model,
        prompt=prompt,
        output=output,
        entity=entity,
    )

    return result.__dict__


@app.post("/v1/sdk/verify")
async def verify_cross_adapter(
    sdk_receipt: Dict[str, Any],
    bridge_receipt: Dict[str, Any],
    x_admin_token: str | None = Header(default=None),
):
    """Verify SDK and bridge receipts are consistent."""
    auth_or_403(x_admin_token)
    return await SDK_SURFACE.verify_cross_adapter(sdk_receipt, bridge_receipt)


# -- StegDB Wiring -----------------------------------------------

@app.post("/v1/stegdb/push")
async def stegdb_push_run(
    session_path: str,
    receipt: Dict[str, Any],
    x_admin_token: str | None = Header(default=None),
):
    """Manually push a run result to StegDB."""
    auth_or_403(x_admin_token)

    return await STEGDB_WIRING.push_run_result(
        session_path=session_path,
        final_receipt=receipt,
        turns=[],
        bridge_entity=BRIDGE_ENTITY,
    )


@app.get("/v1/stegdb/history/{entity_id}")
async def stegdb_history(
    entity_id: str,
    limit: int = 100,
    x_admin_token: str | None = Header(default=None),
):
    """Query StegDB for entity history."""
    auth_or_403(x_admin_token)
    return await STEGDB_WIRING.query_entity_history(entity_id, limit)


# -- Publisher Integration ---------------------------------------

@app.post("/v1/publish/paper")
async def publish_paper(
    title: str,
    content: str,
    authors: List[str],
    venue: str,
    receipt_id: str,
    bcat: Dict[str, Any],
    gcat: Dict[str, Any],
    tags: List[str] = [],
    x_admin_token: str | None = Header(default=None),
):
    """Submit governed output as academic paper."""
    auth_or_403(x_admin_token)

    output = PublishableOutput(
        content=content,
        title=title,
        authors=authors,
        receipt_id=receipt_id,
        bcat=bcat,
        gcat=gcat,
        tags=tags,
        format="paper",
    )

    return await PUBLISHER.submit_paper(output, venue)


@app.post("/v1/publish/social")
async def publish_social(
    title: str,
    content: str,
    platform: str,
    receipt_id: str,
    tags: List[str] = [],
    thread: bool = False,
    x_admin_token: str | None = Header(default=None),
):
    """Post governed output to social media."""
    auth_or_403(x_admin_token)

    output = PublishableOutput(
        content=content,
        title=title,
        authors=[BRIDGE_ENTITY.owner_human],
        receipt_id=receipt_id,
        bcat={},
        gcat={},
        tags=tags,
        format="social",
    )

    return await PUBLISHER.post_social(output, platform, thread)


@app.post("/v1/publish/blog")
async def publish_blog(
    title: str,
    content: str,
    platform: str = "stegverse",
    receipt_id: str = "",
    tags: List[str] = [],
    x_admin_token: str | None = Header(default=None),
):
    """Publish governed output as blog post."""
    auth_or_403(x_admin_token)

    output = PublishableOutput(
        content=content,
        title=title,
        authors=[BRIDGE_ENTITY.owner_human],
        receipt_id=receipt_id,
        bcat={},
        gcat={},
        tags=tags,
        format="blog",
    )

    return await PUBLISHER.publish_blog(output, platform)


# -- AaCT-E Demo Pipeline ----------------------------------------

@app.post("/v1/aacte/experiment")
async def aacte_experiment(
    experiment_id: str,
    hypothesis: str,
    parameters: Dict[str, Any],
    entity_id: str = "",
    x_admin_token: str | None = Header(default=None),
):
    """Run GCAT/BCAT experiment via AaCT-E demo pipeline."""
    auth_or_403(x_admin_token)

    entity = ENTITY_REG.get(entity_id) or BRIDGE_ENTITY

    return await AACTE.run_experiment(
        experiment_id=experiment_id,
        hypothesis=hypothesis,
        parameters=parameters,
        entity=entity,
    )


@app.post("/v1/aacte/validate")
async def aacte_validate(
    experiment_id: str,
    result_data: Dict[str, Any],
    entity_id: str = "",
    x_admin_token: str | None = Header(default=None),
):
    """Validate experiment results."""
    auth_or_403(x_admin_token)

    entity = ENTITY_REG.get(entity_id) or BRIDGE_ENTITY

    return await AACTE.validate_experiment_result(
        experiment_id=experiment_id,
        result_data=result_data,
        entity=entity,
    )


# -- StegCGE Compiler --------------------------------------------

@app.post("/v1/stegcge/register")
async def stegcge_register(
    org_id: str,
    cge_tier: str = "light",
    x_admin_token: str | None = Header(default=None),
):
    """Register org with StegCGE master compiler."""
    auth_or_403(x_admin_token)

    STEGCGE.register_org(org_id, cge_tier)
    return {"status": "registered", "org_id": org_id, "tier": cge_tier}


@app.post("/v1/stegcge/compile")
async def stegcge_compile(x_admin_token: str | None = Header(default=None)):
    """Compile cross-org policy."""
    auth_or_403(x_admin_token)
    return await STEGCGE.compile_policy()


@app.get("/v1/stegcge/status")
async def stegcge_status(x_admin_token: str | None = Header(default=None)):
    """Get StegCGE compiler status."""
    auth_or_403(x_admin_token)
    return STEGCGE.get_master_status()


@app.get("/v1/stegcge/health/{org_id}")
async def stegcge_org_health(
    org_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Check org health via StegCGE."""
    auth_or_403(x_admin_token)
    return await STEGCGE.check_org_health(org_id)


@app.post("/v1/stegcge/repair")
async def stegcge_repair(
    org_id: str,
    x_admin_token: str | None = Header(default=None),
):
    """Direct repair for failed org."""
    auth_or_403(x_admin_token)

    status = await STEGCGE.check_org_health(org_id)
    return await STEGCGE.direct_repair(org_id, status)
