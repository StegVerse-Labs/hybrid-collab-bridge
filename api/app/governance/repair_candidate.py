"""Bounded repair-candidate construction for failed artifact integrity.

A repair candidate preserves the original run and artifact identity evidence,
but does not overwrite the original artifact, execute a repair, or grant commit
authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Any, Optional

from .artifact_integrity import ArtifactIntegrityResult


@dataclass(frozen=True)
class RepairCandidate:
    repair_candidate_id: str
    original_run_id: str
    original_artifact_id: Optional[str]
    original_content_sha256: str
    required_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    repair_scope: str
    status: str = "DECLARED"
    admissibility_result: str = "PENDING"
    commit_time_validity: str = "PENDING"
    action_ref: None = None
    final_receipt_id: None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_repair_candidate(
    *,
    run_id: str,
    artifact_id: Optional[str],
    integrity: ArtifactIntegrityResult,
) -> RepairCandidate:
    """Declare a deterministic repair candidate from failed integrity evidence."""
    if integrity.decision not in {"NEEDS_REPAIR", "FAIL_CLOSED"}:
        raise ValueError("Repair candidates require NEEDS_REPAIR or FAIL_CLOSED evidence.")
    if not run_id.strip():
        raise ValueError("run_id is required to preserve repair continuity.")

    seed = "|".join(
        [
            run_id,
            artifact_id or "",
            integrity.content_sha256,
            integrity.decision,
            *integrity.missing_sections,
        ]
    )
    repair_id = f"repair-{sha256(seed.encode('utf-8')).hexdigest()[:24]}"
    scope = (
        "supply missing declared sections without changing preserved original evidence"
        if integrity.decision == "NEEDS_REPAIR"
        else "replace empty or structurally unavailable artifact while preserving original evidence"
    )

    return RepairCandidate(
        repair_candidate_id=repair_id,
        original_run_id=run_id,
        original_artifact_id=artifact_id,
        original_content_sha256=integrity.content_sha256,
        required_sections=integrity.required_sections,
        missing_sections=integrity.missing_sections,
        repair_scope=scope,
    )
