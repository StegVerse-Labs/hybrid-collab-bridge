"""Governed AI Entity identity for StegVerse ecosystem."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import hashlib
import json


@dataclass(frozen=True)
class EntityIdentity:
    entity_id: str
    entity_type: str
    org_id: str
    owner_human: str
    owner_ai: Optional[str] = None
    capability_set: List[str] = field(default_factory=list)
    invariant_hash: str = ""
    governance_scope: str = "internal"
    compensation_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "org_id": self.org_id,
            "owner_human": self.owner_human,
            "owner_ai": self.owner_ai,
            "capability_set": self.capability_set,
            "invariant_hash": self.invariant_hash,
            "governance_scope": self.governance_scope,
            "compensation_rate": self.compensation_rate,
        }

    def compute_invariant_hash(self, invariants: List[str]) -> str:
        payload = json.dumps(sorted(invariants), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class EntityRegistry:
    def __init__(self, org_id: str):
        self.org_id = org_id
        self._entities: Dict[str, EntityIdentity] = {}

    def register(self, entity: EntityIdentity) -> None:
        if entity.org_id != self.org_id:
            raise ValueError(f"Entity org mismatch: {entity.org_id} != {self.org_id}")
        self._entities[entity.entity_id] = entity

    def get(self, entity_id: str) -> Optional[EntityIdentity]:
        return self._entities.get(entity_id)

    def list_by_type(self, entity_type: str) -> List[EntityIdentity]:
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def all(self) -> List[EntityIdentity]:
        return list(self._entities.values())
