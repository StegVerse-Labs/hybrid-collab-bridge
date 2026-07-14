"""Deterministic run-boundary policy for internal governed proposals.

This module separates provider admission, artifact integrity, accepted-result
-ingestion eligibility, exception review, and bounded CGE evidence. It does not
execute, publish, delegate, or issue final receipts.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Optional

from .artifact_integrity import ArtifactIntegrityResult


@dataclass(frozen=True)
class RunBoundaryDecision:
    status: str
    may_ingest_accepted_result: bool
    preserve_governance_event: bool
    requires_human: bool
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide_run_boundary(
    *,
    provider_status: str,
    provider_decision: str,
    integrity: Optional[ArtifactIntegrityResult],
    human_gate: bool = False,
) -> RunBoundaryDecision:
    """Return the bounded status and accepted-result ingestion decision.

    Provider denial/deferment remain observable governance events, but are not
    accepted result ingestion. An allowed candidate must pass artifact integrity
    before it may be ingested as an accepted run result.
    """
    if provider_status == "DENIED" or provider_decision == "deny":
        return RunBoundaryDecision(
            status="ADMISSIBILITY_FAILED",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=False,
            reasoning="Provider admission denied the candidate.",
        )

    if provider_status == "DEFERRED" or provider_decision == "defer":
        return RunBoundaryDecision(
            status="EXCEPTION_REVIEW",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=True,
            reasoning="Provider admission deferred the candidate to exception review.",
        )

    if provider_decision != "allow":
        return RunBoundaryDecision(
            status="ADMISSIBILITY_FAILED",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=False,
            reasoning="Provider admission did not produce an allowed candidate.",
        )

    if integrity is None:
        return RunBoundaryDecision(
            status="INTEGRITY_FAILED",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=False,
            reasoning="Allowed candidate has no artifact-integrity evidence.",
        )

    if integrity.decision == "FAIL_CLOSED":
        return RunBoundaryDecision(
            status="INTEGRITY_FAILED",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=False,
            reasoning=integrity.reasoning,
        )

    if integrity.decision == "NEEDS_REPAIR":
        return RunBoundaryDecision(
            status="NEEDS_REPAIR",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=False,
            reasoning=integrity.reasoning,
        )

    if human_gate:
        return RunBoundaryDecision(
            status="EXCEPTION_REVIEW",
            may_ingest_accepted_result=False,
            preserve_governance_event=True,
            requires_human=True,
            reasoning="Explicit exception review requested after integrity passed.",
        )

    return RunBoundaryDecision(
        status="OK",
        may_ingest_accepted_result=True,
        preserve_governance_event=True,
        requires_human=False,
        reasoning="Provider admission and declared artifact integrity passed.",
    )


def build_integrity_ledger_payload(
    *,
    run_id: Optional[str],
    artifact_id: Optional[str],
    integrity: ArtifactIntegrityResult,
    boundary: RunBoundaryDecision,
) -> dict[str, Any]:
    """Build bounded CGE evidence without claiming downstream admissibility."""
    return {
        "type": "artifact_integrity_evaluation",
        "run_id": run_id,
        "artifact_id": artifact_id,
        "content_sha256": integrity.content_sha256,
        "required_sections": list(integrity.required_sections),
        "missing_sections": list(integrity.missing_sections),
        "integrity_decision": integrity.decision,
        "run_status": boundary.status,
        "accepted_result_ingestion_permitted": boundary.may_ingest_accepted_result,
        "downstream_admissibility": "PENDING",
        "reasoning": boundary.reasoning,
    }
