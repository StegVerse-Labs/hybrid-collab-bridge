"""Bounded transition-candidate envelope for Ecosystem-Delegation.

This module prepares an internal bridge result for the next governed boundary.
It preserves identity and evidence references but does not delegate, execute,
publish, or issue a final receipt.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping, Optional


@dataclass(frozen=True)
class DelegationCandidateEnvelope:
    schema_version: str
    candidate_id: str
    transition_id: str
    run_id: str
    event_id: str
    origin_manifest_id: str
    source_repository: str
    source_adapter: str
    target_repository: str
    target_boundary: str
    lifecycle_status: str
    bridge_status: str
    content_sha256: str
    integrity_decision: str
    integrity_evidence_ref: Optional[str]
    repair_candidate_ref: Optional[str]
    evidence_refs: tuple[str, ...]
    admissibility_result: str
    commit_time_validity: str
    action_ref: None
    final_receipt_id: None
    execution_authority: bool
    publication_authority: bool
    delegation_authority: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def build_delegation_candidate(
    *,
    transition_id: str,
    run_id: str,
    event_id: str,
    origin_manifest_id: str,
    bridge_status: str,
    content_sha256: str,
    integrity_decision: str,
    evidence_refs: Iterable[str] = (),
    integrity_evidence_ref: Optional[str] = None,
    repair_candidate_ref: Optional[str] = None,
) -> DelegationCandidateEnvelope:
    """Create a deterministic candidate for the Ecosystem-Delegation boundary."""
    transition_id = _required_text(transition_id, "transition_id")
    run_id = _required_text(run_id, "run_id")
    event_id = _required_text(event_id, "event_id")
    origin_manifest_id = _required_text(origin_manifest_id, "origin_manifest_id")
    content_sha256 = _required_text(content_sha256, "content_sha256")
    if len(content_sha256) != 64:
        raise ValueError("content_sha256 must be a 64-character SHA-256 hex digest")

    refs = tuple(dict.fromkeys(str(ref).strip() for ref in evidence_refs if str(ref).strip()))
    lifecycle = {
        "OK": "READY",
        "NEEDS_REPAIR": "VERIFICATION_REQUIRED",
        "INTEGRITY_FAILED": "FAIL_CLOSED",
        "ADMISSIBILITY_FAILED": "BLOCKED",
        "EXCEPTION_REVIEW": "VERIFICATION_REQUIRED",
    }.get(bridge_status, "FAIL_CLOSED")

    seed = "|".join(
        [
            transition_id,
            run_id,
            event_id,
            origin_manifest_id,
            bridge_status,
            content_sha256,
            integrity_decision,
            *refs,
        ]
    )
    candidate_id = f"hcb-delegation-{sha256(seed.encode('utf-8')).hexdigest()[:24]}"

    return DelegationCandidateEnvelope(
        schema_version="1.0",
        candidate_id=candidate_id,
        transition_id=transition_id,
        run_id=run_id,
        event_id=event_id,
        origin_manifest_id=origin_manifest_id,
        source_repository="StegVerse-Labs/hybrid-collab-bridge",
        source_adapter="internal_llm_adapter",
        target_repository="StegVerse-Labs/Ecosystem-Delegation",
        target_boundary="delegation_intake",
        lifecycle_status=lifecycle,
        bridge_status=bridge_status,
        content_sha256=content_sha256,
        integrity_decision=integrity_decision,
        integrity_evidence_ref=integrity_evidence_ref,
        repair_candidate_ref=repair_candidate_ref,
        evidence_refs=refs,
        admissibility_result="PENDING",
        commit_time_validity="PENDING",
        action_ref=None,
        final_receipt_id=None,
        execution_authority=False,
        publication_authority=False,
        delegation_authority=False,
    )
