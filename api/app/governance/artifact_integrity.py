"""Deterministic artifact-integrity checks for internal LLM proposals.

This module does not grant admissibility or execution authority. It only
verifies that a candidate artifact satisfies its declared structural contract
before the candidate may proceed to the next governed boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ArtifactIntegrityResult:
    decision: str
    content_sha256: str
    required_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]
    empty: bool
    reasoning: str

    @property
    def passed(self) -> bool:
        return self.decision == "ALLOW_NEXT_BOUNDARY"

    def to_dict(self) -> dict:
        return asdict(self) | {"passed": self.passed}


def _normalize_heading(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def evaluate_artifact_integrity(
    content: str,
    required_sections: Sequence[str] | Iterable[str] = (),
) -> ArtifactIntegrityResult:
    """Evaluate a text artifact against its declared section contract.

    The check is deliberately deterministic and bounded:
    - empty content fails closed;
    - every declared section must be present;
    - no diagnosis, semantic correctness, execution, or publication decision
      is made here;
    - the resulting SHA-256 supports later receipt and replay correlation.
    """

    raw = content if isinstance(content, str) else str(content)
    digest = sha256(raw.encode("utf-8")).hexdigest()
    required = tuple(dict.fromkeys(str(item).strip() for item in required_sections if str(item).strip()))
    normalized_content = _normalize_heading(raw)
    missing = tuple(
        section
        for section in required
        if _normalize_heading(section) not in normalized_content
    )
    empty = not raw.strip()

    if empty:
        decision = "FAIL_CLOSED"
        reasoning = "Artifact content is empty."
    elif missing:
        decision = "NEEDS_REPAIR"
        reasoning = "Artifact is missing one or more declared required sections."
    else:
        decision = "ALLOW_NEXT_BOUNDARY"
        reasoning = "Declared structural requirements are present; downstream admissibility remains pending."

    return ArtifactIntegrityResult(
        decision=decision,
        content_sha256=digest,
        required_sections=required,
        missing_sections=missing,
        empty=empty,
        reasoning=reasoning,
    )
