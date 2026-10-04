"""Pydantic models with CGE receipt and artifact-integrity integration."""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

StrategyName = Literal["consensus", "committee"]
Decision = Literal["allow", "deny", "defer"]
RunStatus = Literal[
    "OK",
    "NEEDS_REPAIR",
    "INTEGRITY_FAILED",
    "ADMISSIBILITY_FAILED",
    "EXCEPTION_REVIEW",
    "PAUSED_FOR_REVIEW",
    "DENIED",
    "DEFERRED",
]


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


class ArtifactManifest(BaseModel):
    """Declared structural contract for one generated text artifact.

    This declaration controls integrity evaluation only. It does not grant
    semantic correctness, admissibility, execution, publication, delegation,
    or final-receipt authority.
    """
    artifact_id: Optional[str] = None
    artifact_type: Literal["text"] = "text"
    required_sections: List[str] = Field(default_factory=list)


class IntegrityEvidence(BaseModel):
    """Deterministic artifact-integrity evidence returned by the bridge."""
    decision: Literal["ALLOW_NEXT_BOUNDARY", "NEEDS_REPAIR", "FAIL_CLOSED"]
    content_sha256: str
    required_sections: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    empty: bool
    reasoning: str
    passed: bool


class ExternalInferenceObservationRef(BaseModel):
    """Retained, non-authoritative evidence for one external provider response."""
    observation_id: str
    provider: str
    model: Optional[str] = None
    request_correlation: str
    response_sha256: str
    observation_state: Literal["RETAINED", "FAILED", "INDETERMINATE"]
    authority_effect: Literal["NONE"] = "NONE"


class EcosystemChatInferenceSession(BaseModel):
    """Receipt #1-bound ephemeral session; provider outputs remain evidence only."""
    schema_name: Literal["stegverse.hybrid-collab.ecosystem-chat-external-inference-session/v1"] = Field(
        default="stegverse.hybrid-collab.ecosystem-chat-external-inference-session/v1",
        alias="schema",
    )
    session_id: str
    node_id: str
    receipt_1_sha256: str
    prompt_sha256: str
    observations: List[ExternalInferenceObservationRef]
    authority_effect: Literal["NONE"] = "NONE"

    def retained_observation_ids(self) -> set[str]:
        return {
            item.observation_id
            for item in self.observations
            if item.observation_state == "RETAINED"
        }

    def require_retained_references(self, observation_refs: List[str]) -> None:
        """Fail closed unless comparison/synthesis cites retained observations only."""
        retained = self.retained_observation_ids()
        if not observation_refs:
            raise ValueError("comparison requires retained observation references")
        if len(set(observation_refs)) != len(observation_refs):
            raise ValueError("comparison observation references must be unique")
        missing = [ref for ref in observation_refs if ref not in retained]
        if missing:
            raise ValueError(
                "comparison references missing or non-retained evidence: "
                + ",".join(missing)
            )


class ExternalInferenceComparisonInput(BaseModel):
    """Reference-only input to existing collaboration/synthesis logic."""
    session_id: str
    observation_refs: List[str]
    authority_effect: Literal["NONE"] = "NONE"


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
    artifact_manifest: Optional[ArtifactManifest] = None


class Turn(BaseModel):
    """A single expert turn with receipt."""
    who: str
    output: str
    receipt: Optional[ReceiptRef] = None
    bcat: Optional[Dict[str, Any]] = None
    gcat: Optional[Dict[str, Any]] = None
    decision: Optional[Decision] = None


class RunResponse(BaseModel):
    """Response with governance and artifact-integrity evidence."""
    status: RunStatus
    session_path: str
    strategy: StrategyName
    turns: List[Turn] = Field(default_factory=list)
    final: Optional[str] = None
    final_receipt: Optional[ReceiptRef] = None
    final_bcat: Optional[Dict[str, Any]] = None
    final_gcat: Optional[Dict[str, Any]] = None
    integrity: Optional[IntegrityEvidence] = None
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


# -- Discovery models ---------------------------------------------------------

class DiscoveryRequest(BaseModel):
    """Request to discover or query a provider."""
    query: str = Field(..., description="Provider name, type, or 'other' for discovery scan")
    scan_type: Literal["auto", "local", "env", "network", "query"] = "auto"


class DiscoveryResultItem(BaseModel):
    """A single discovery result."""
    provider_id: str
    provider_name: str
    provider_type: str
    status: Literal["available", "unavailable", "discoverable", "denied"]
    reason: str
    connection_method: Literal["local", "env", "network", "manual", "none"]
    instructions: List[str] = Field(default_factory=list)
    config_template: Dict[str, Any] = Field(default_factory=dict)
    requires_network: bool = True
    requires_api_key: bool = True
    estimated_cost_tier: str = "unknown"


class DiscoveryResponse(BaseModel):
    """Response from provider discovery."""
    scan_type: str
    results: List[DiscoveryResultItem]
    total_found: int
    total_available: int
    total_discoverable: int
    total_denied: int


class ProviderConnectRequest(BaseModel):
    """Request to connect a discovered provider."""
    provider_id: str
    provider_type: str
    config: Dict[str, Any]
    test_connection: bool = True
