"""Stdlib-only, vendorable HCB contract. Outputs are never authority (authority_effect NONE)."""
from .capability import (
    ALLOW,
    AUTHORITY_EFFECT,
    DENY,
    FAIL_CLOSED,
    MAPPING_VERSION,
    OWNING_EXISTING_GOAL,
    RECOGNIZED_MAPPINGS,
    SCHEMA_ID,
    ContractResult,
    ProtocolAdapter,
    ProtocolMapping,
    normalize_capability_descriptor,
)

__all__ = [
    "ALLOW",
    "AUTHORITY_EFFECT",
    "DENY",
    "FAIL_CLOSED",
    "MAPPING_VERSION",
    "OWNING_EXISTING_GOAL",
    "RECOGNIZED_MAPPINGS",
    "SCHEMA_ID",
    "ContractResult",
    "ProtocolAdapter",
    "ProtocolMapping",
    "normalize_capability_descriptor",
]
