"""Pydantic models with CGE receipt integration."""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

StrategyName = Literal["consensus", "committee"]
Decision = Literal["allow", "deny", "defer"]


class EntityRef(BaseModel):
    """Reference to a governed entity."""
    entity_id: str
    entity_type: str
    org_id: str
    invariant_hash: str


class ReceiptRef(BaseModel):
    """Reference to a CGE receipt."""
    receipt_id: str
    ledger_entry_id: str
    entry_hash: str
    decision: Decision
    verified: bool = False


class RunRequest(BaseModel):
    """Request to run a governed collaboration."""
    slug: str = Field(..., description="folder slug under sessions/YYYY-MM-DD/")
    question: str
    context: Optional[str] = None
    experts: List[str] = Field(default_factory=lambda: ["claude"])
    strategy: StrategyName = "consensus"
    human_gate: bool = Field(default=False, description="Exception-only human review")
    temperature: float = 0.4
    entity_id: Optional[str] = None
    trace_level: Literal["minimal", "full", "debug"] = "full"


class Turn(BaseModel):
    """A single expert turn with receipt."""
    who: str
    output: str
    receipt: Optional[ReceiptRef] = None
    bcat: Optional[Dict[str, Any]] = None
    gcat: Optional[Dict[str, Any]] = None
    decision: Optional[Decision] = None


class RunResponse(BaseModel):
    """Response with full governance trace."""
    status: Literal["OK", "PAUSED_FOR_REVIEW", "DENIED", "DEFERRED"]
    session_path: str
    strategy: StrategyName
    turns: List[Turn] = []
    final: Optional[str] = None
    final_receipt: Optional[ReceiptRef] = None
    final_bcat: Optional[Dict[str, Any]] = None
    final_gcat: Optional[Dict[str, Any]] = None
    chain_id: Optional[str] = None
    requires_human: bool = False
    requires_ai_quorum: bool = False
    reasoning: Optional[str] = None


class ContinueRequest(BaseModel):
    """Request to continue a deferred session."""
    session_path: str
    approval: Literal["human_approve", "ai_approve", "quorum_approve", "reject"]
    approver_entity_id: str
    approver_type: Literal["human_operator", "ai_entity"]
    notes: Optional[str] = None
