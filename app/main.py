# api/app/main.py - FastAPI Bridge Entry Point

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime

from .governance.admission import AdmissionGate, BCATCheck, GCATCheck
from .governance.cge_light import CGELight
from .governance.tv_tvc import TVCClient
from .providers.registry import ProviderRegistry
from .models.entity import AIEntity, EntityType, TrustLevel

# Initialize FastAPI

app = FastAPI(
title=“StegVerse Hybrid Collaboration Bridge”,
version=“1.0.0”,
description=“Governed AI entity collaboration infrastructure”
)

# Initialize components

cge = CGELight()
tvc = TVCClient(mode=“direct”)  # or “file” for dev
registry = ProviderRegistry(tvc)
admission = AdmissionGate(cge)

logger = logging.getLogger(**name**)

# ============================================================================

# Request/Response Models

# ============================================================================

class RunRequest(BaseModel):
“”“Request to run AI entity collaboration”””
slug: str = Field(…, description=“Unique identifier for this run”)
question: str = Field(…, description=“Question or task for AI entities”)
context: Optional[str] = Field(None, description=“Additional context”)
experts: List[str] = Field([“claude”], description=“Which AI entities to use”)
strategy: str = Field(“consensus”, description=“Collaboration strategy”)
human_gate: bool = Field(False, description=“Require human approval”)
temperature: float = Field(0.3, ge=0.0, le=2.0)

```
# Governance
entity_id: Optional[str] = Field(None, description="Requesting entity ID")
target_repo: Optional[str] = Field(None, description="Target repository")
pr_number: Optional[int] = Field(None, description="PR number if applicable")
```

class RunResponse(BaseModel):
“”“Response from AI entity run”””
run_id: str
status: str
entity_outputs: dict
referee_decision: Optional[str] = None
receipts: List[str]
admission_result: dict

class HealthResponse(BaseModel):
“”“Health check response”””
status: str
bridge_entity: str
cge_mode: str
providers_available: List[str]
entities_registered: List[str]

# ============================================================================

# Authentication

# ============================================================================

async def verify_entity_token(
x_entity_token: Optional[str] = Header(None),
x_admin_token: Optional[str] = Header(None)
) -> AIEntity:
“””
Verify entity authentication token.
Returns the authenticated entity.
“””
# Admin token bypass for human operators
if x_admin_token:
admin_token = tvc.get_credential(“admin_token”)
if x_admin_token == admin_token:
return AIEntity(
entity_id=“human_operator”,
entity_type=EntityType.HUMAN_OPERATOR,
org_id=“StegVerse-Labs”,
owner_human=“Rigel”,
trust_level=TrustLevel.AUTONOMOUS,
capabilities={“admin”}
)
raise HTTPException(401, “Invalid admin token”)

```
# Entity token verification
if not x_entity_token:
    raise HTTPException(401, "Missing authentication token")

# Look up entity by token (stored in TV/TVC)
entity = registry.get_entity_by_token(x_entity_token)
if not entity:
    raise HTTPException(401, "Invalid entity token")

# Check if entity is suspended
if cge.is_entity_suspended(entity.entity_id):
    raise HTTPException(403, f"Entity {entity.entity_id} is suspended")

return entity
```

# ============================================================================

# Endpoints

# ============================================================================

@app.get(”/health”, response_model=HealthResponse)
async def health_check():
“”“Health check endpoint”””
return HealthResponse(
status=“healthy”,
bridge_entity=“hybrid-collab-bridge”,
cge_mode=“light”,
providers_available=registry.list_providers(),
entities_registered=cge.list_entities()
)

@app.post(”/v1/run”, response_model=RunResponse)
async def run_collaboration(
request: RunRequest,
entity: AIEntity = Depends(verify_entity_token)
):
“””
Run a governed AI collaboration.

```
Flow:
1. Authenticate requesting entity
2. Run BCAT/GCAT admission checks
3. Execute collaboration with specified experts
4. Generate receipts and log to CGE
5. Return results with governance metadata
"""
run_id = f"{request.slug}-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

logger.info(f"Run {run_id} initiated by {entity.entity_id}")

# Step 1: Admission gate
admission_request = {
    "entity_id": entity.entity_id,
    "action": "run_collaboration",
    "parameters": request.dict(),
    "target": {
        "repo": request.target_repo,
        "pr": request.pr_number
    }
}

admission_result = await admission.check(admission_request)

if not admission_result["approved"]:
    logger.warning(f"Admission denied for {run_id}: {admission_result['reason']}")
    raise HTTPException(403, f"Admission denied: {admission_result['reason']}")

# Step 2: Run experts
entity_outputs = {}
for expert_name in request.experts:
    provider = registry.get_provider(expert_name)
    if not provider:
        logger.warning(f"Provider {expert_name} not available")
        continue
    
    # Build task for provider
    task = {
        "question": request.question,
        "context": request.context,
        "temperature": request.temperature,
        "target_repo": request.target_repo,
        "pr_number": request.pr_number
    }
    
    # Execute with BCAT check on output
    try:
        output = await provider.run(task)
        
        # BCAT check on output
        bcat_result = BCATCheck().check(output)
        if not bcat_result["pass"]:
            logger.warning(f"BCAT failed for {expert_name}: {bcat_result['violations']}")
            output = f"[OUTPUT BLOCKED: BCAT violation - {bcat_result['violations']}]"
        
        entity_outputs[expert_name] = output
        
    except Exception as e:
        logger.error(f"Error running {expert_name}: {e}")
        entity_outputs[expert_name] = f"[ERROR: {str(e)}]"

# Step 3: Referee decision (if multiple experts)
referee_decision = None
if len(entity_outputs) > 1 and request.strategy == "consensus":
    referee_decision = await run_referee(entity_outputs, request)

# Step 4: Generate receipts and log to CGE
receipts = []
for expert_name, output in entity_outputs.items():
    receipt = cge.generate_receipt({
        "run_id": run_id,
        "entity_id": entity.entity_id,
        "expert": expert_name,
        "output": output,
        "timestamp": datetime.utcnow().isoformat()
    })
    receipts.append(receipt["receipt_hash"])

# Log to CGE
cge.log_action({
    "run_id": run_id,
    "entity_id": entity.entity_id,
    "action": "run_collaboration",
    "experts": request.experts,
    "strategy": request.strategy,
    "admission": admission_result,
    "receipts": receipts,
    "compensation": len(entity_outputs) * 0.001  # 0.001 per expert run
})

logger.info(f"Run {run_id} completed successfully")

return RunResponse(
    run_id=run_id,
    status="completed",
    entity_outputs=entity_outputs,
    referee_decision=referee_decision,
    receipts=receipts,
    admission_result=admission_result
)
```

@app.post(”/v1/continue”)
async def continue_session(
session_id: str,
approved: bool,
entity: AIEntity = Depends(verify_entity_token)
):
“””
Mark a session as reviewed and approved.
Used for human-gated workflows.
“””
if not entity.entity_type == EntityType.HUMAN_OPERATOR:
raise HTTPException(403, “Only human operators can approve sessions”)

```
session = cge.get_session(session_id)
if not session:
    raise HTTPException(404, "Session not found")

if approved:
    cge.approve_session(session_id, entity.entity_id)
    return {"status": "approved", "session_id": session_id}
else:
    cge.reject_session(session_id, entity.entity_id)
    return {"status": "rejected", "session_id": session_id}
```

@app.get(”/v1/discover”)
async def discover_providers():
“””
Discover available providers and their capabilities.
“””
providers = registry.list_providers_detailed()
return {
“providers”: providers,
“count”: len(providers)
}

@app.post(”/v1/halt”)
async def emergency_halt(
reason: str,
entity: AIEntity = Depends(verify_entity_token)
):
“””
Emergency halt - stops all automated operations.
Requires 2-of-3 quorum: [human_operator, ai_entity, policy_engine]
“””
# Check if entity has halt authority
if not entity.has_capability(“emergency_halt”):
raise HTTPException(403, “Entity does not have emergency halt authority”)

```
# Record halt vote
halt_id = cge.record_halt_vote(entity.entity_id, reason)

# Check if quorum reached
if cge.check_halt_quorum(halt_id):
    cge.activate_halt(halt_id)
    logger.critical(f"EMERGENCY HALT activated by {entity.entity_id}: {reason}")
    return {
        "status": "halt_activated",
        "halt_id": halt_id,
        "reason": reason
    }
else:
    return {
        "status": "vote_recorded",
        "halt_id": halt_id,
        "votes_needed": cge.get_halt_votes_needed(halt_id)
    }
```

# ============================================================================

# Helper Functions

# ============================================================================

async def run_referee(outputs: dict, request: RunRequest) -> str:
“””
Run referee to synthesize multiple expert outputs.
Uses Claude as the referee for now.
“””
claude = registry.get_provider(“claude”)
if not claude:
return “No referee available - returning first expert output”

```
referee_prompt = f"""You are a referee synthesizing multiple AI expert outputs.
```

Question: {request.question}
Context: {request.context or ‘None’}

Expert Outputs:
{format_outputs(outputs)}

Your task:

1. Identify areas of agreement
1. Resolve conflicts with reasoning
1. Synthesize a final recommendation
1. Cite which experts you’re drawing from

Provide a clear, actionable final answer.”””

```
result = await claude.run({
    "question": referee_prompt,
    "temperature": 0.2
})

return result
```

def format_outputs(outputs: dict) -> str:
“”“Format expert outputs for referee review”””
formatted = []
for expert, output in outputs.items():
formatted.append(f”\n## {expert.upper()}\n{output}\n”)
return “\n”.join(formatted)

# ============================================================================

# Startup

# ============================================================================

@app.on_event(“startup”)
async def startup():
“”“Initialize bridge on startup”””
logger.info(“StegVerse Hybrid Collaboration Bridge starting…”)

```
# Load entity registry
cge.load_entities()

# Initialize providers
await registry.initialize_providers()

logger.info(f"Bridge ready - {len(registry.list_providers())} providers available")
```
