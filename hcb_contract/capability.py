"""Vendorable, stdlib-only HCB capability contract (v1).

Pure functions only: no network, no filesystem writes, no credentials, no
third-party imports. Every output carries ``authority_effect: NONE``; HCB is an
optional translation surface and never a mandatory hop or an authority.
Authority remains with Interlock/InTr via SDK manifest submission.

Non-ALLOW results carry the six conformance fields required by
StegVerse-org/.github docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md:
failure_code, failed_predicate, required_evidence_or_repair, retry_entrypoint,
owning_existing_goal, next_attempt.

Self-learning of novel protocols is NOT claimed. A novel input shape returns a
candidate mapping as non-authorizing evidence together with FAIL_CLOSED.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

SCHEMA_ID = "stegverse.hybrid-collab.capability-descriptor/v1"
RESULT_SCHEMA_ID = "stegverse.hybrid-collab.contract-result/v1"
SDK_INPUT_CANDIDATE_SCHEMA_ID = "stegverse.hybrid-collab.sdk-input-candidate/v1"
MAPPING_VERSION = "v1"
OWNING_EXISTING_GOAL = "HCB-VERSIONED-CONTRACT-038"
AUTHORITY_EFFECT = "NONE"

ALLOW = "ALLOW"
DENY = "DENY"
FAIL_CLOSED = "FAIL_CLOSED"

SDK_RETRY_ENTRYPOINT = "StegVerse-SDK manifest submission (target_ref bridge:hybrid-collab)"
NORMALIZE_RETRY_ENTRYPOINT = "hcb_contract.capability.normalize_capability_descriptor"
TRANSLATE_RETRY_ENTRYPOINT = "hcb_contract.capability.ProtocolAdapter.translate"

# Mirrors api/app/models.py WorkClass / MediaType / EntitlementState / RoutingDisposition.
WORK_CLASSES = ("text", "reasoning", "code", "image", "video", "audio", "science", "research", "data", "other")
MEDIA_TYPES = ("text", "code", "image", "video", "audio", "structured_data", "binary", "other")
ENTITLEMENT_STATES = ("NOT_REQUIRED", "ENTITLED", "NOT_ENTITLED", "UNKNOWN")
ROUTING_DISPOSITIONS = (
    "AVAILABLE",
    "UPGRADE_REQUIRED",
    "PURCHASE_REQUIRED",
    "PROVIDER_UNAVAILABLE",
    "DENIED",
    "ENTITLEMENT_UNKNOWN",
)

DESCRIPTOR_DEFAULTS: Dict[str, Any] = {
    "input_media": [],
    "output_media": [],
    "model": None,
    "entitlement_state": "UNKNOWN",
    "routing_disposition": "ENTITLEMENT_UNKNOWN",
    "required_tier": None,
    "execution_constraints": {},
    "evidence_return": "RETAINED_OBSERVATION_REQUIRED",
    "authority_effect": AUTHORITY_EFFECT,
}
DESCRIPTOR_REQUIRED = ("capability_id", "work_class", "provider")
DESCRIPTOR_FIELDS = ("schema",) + DESCRIPTOR_REQUIRED + tuple(DESCRIPTOR_DEFAULTS)

_SECRET_KEY = re.compile(
    r"(^|[_\-.])(api[_\-]?key|apikey|access[_\-]?token|auth[_\-]?token|refresh[_\-]?token|token|"
    r"secret|client[_\-]?secret|password|passwd|authorization|credentials?|bearer|private[_\-]?key|cookie)($|[_\-.])",
    re.IGNORECASE,
)


def is_secret_like_key(key: str) -> bool:
    return bool(_SECRET_KEY.search(str(key)))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _strip_secrets(value: Any) -> Tuple[Any, int]:
    """Return a copy with secret-like keys removed and the number removed."""
    if isinstance(value, Mapping):
        out: Dict[str, Any] = {}
        removed = 0
        for k, v in value.items():
            if is_secret_like_key(k):
                removed += 1
                continue
            out[str(k)], n = _strip_secrets(v)
            removed += n
        return out, removed
    if isinstance(value, (list, tuple)):
        items = []
        removed = 0
        for v in value:
            c, n = _strip_secrets(v)
            items.append(c)
            removed += n
        return items, removed
    return value, 0


@dataclass(frozen=True)
class ContractResult:
    """Outcome of a contract operation. ``authority_effect`` is always NONE."""

    operation: str
    disposition: str
    output: Optional[Dict[str, Any]] = None
    input_sha256: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    failure_code: Optional[str] = None
    failed_predicate: Optional[str] = None
    required_evidence_or_repair: Optional[str] = None
    retry_entrypoint: Optional[str] = None
    owning_existing_goal: Optional[str] = None
    next_attempt: Optional[str] = None

    @property
    def allowed(self) -> bool:
        return self.disposition == ALLOW

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "schema": RESULT_SCHEMA_ID,
            "operation": self.operation,
            "disposition": self.disposition,
            "output": self.output,
            "input_sha256": self.input_sha256,
            "evidence": self.evidence,
            "authority_effect": AUTHORITY_EFFECT,
        }
        if self.disposition != ALLOW:
            data.update(
                {
                    "failure_code": self.failure_code,
                    "failed_predicate": self.failed_predicate,
                    "required_evidence_or_repair": self.required_evidence_or_repair,
                    "retry_entrypoint": self.retry_entrypoint,
                    "owning_existing_goal": self.owning_existing_goal,
                    "next_attempt": self.next_attempt,
                }
            )
        return data


def _non_allow(
    operation: str,
    disposition: str,
    failure_code: str,
    failed_predicate: str,
    required_evidence_or_repair: str,
    retry_entrypoint: str,
    next_attempt: str,
    input_sha256: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
) -> ContractResult:
    return ContractResult(
        operation=operation,
        disposition=disposition,
        input_sha256=input_sha256,
        evidence=evidence or {},
        failure_code=failure_code,
        failed_predicate=failed_predicate,
        required_evidence_or_repair=required_evidence_or_repair,
        retry_entrypoint=retry_entrypoint,
        owning_existing_goal=OWNING_EXISTING_GOAL,
        next_attempt=next_attempt,
    )


def normalize_capability_descriptor(descriptor: Mapping[str, Any]) -> ContractResult:
    """Validate and normalize a capability descriptor to the v1 contract.

    A missing ``schema`` is treated as v1 for compatibility with existing
    CapabilityDescriptor callers; any other schema id is a version mismatch.
    """
    op = "normalize_capability_descriptor"
    if not isinstance(descriptor, Mapping):
        return _non_allow(
            op, DENY, "INVALID_CAPABILITY_DESCRIPTOR", "descriptor_is_object",
            "submit a JSON object matching schemas/capability_descriptor.v1.schema.json",
            NORMALIZE_RETRY_ENTRYPOINT, "resubmit a corrected descriptor",
        )
    input_sha = sha256_of(dict(descriptor))

    def deny(code: str, predicate: str, repair: str) -> ContractResult:
        return _non_allow(op, DENY, code, predicate, repair, NORMALIZE_RETRY_ENTRYPOINT,
                          "resubmit a corrected descriptor", input_sha256=input_sha)

    schema = descriptor.get("schema", descriptor.get("schema_id", SCHEMA_ID))
    if schema != SCHEMA_ID:
        return deny("CAPABILITY_SCHEMA_VERSION_MISMATCH", "schema == " + SCHEMA_ID,
                    "re-express the descriptor in " + SCHEMA_ID)

    secret_keys = [k for k in descriptor if is_secret_like_key(k)]
    if secret_keys:
        return deny("CREDENTIAL_MATERIAL_IN_DESCRIPTOR", "descriptor_contains_no_credentials",
                    "remove credential-like fields; descriptors carry metadata only")

    allowed = set(DESCRIPTOR_FIELDS) | {"schema_id"}
    unknown = sorted(k for k in descriptor if k not in allowed)
    if unknown:
        return deny("UNKNOWN_DESCRIPTOR_FIELD", "descriptor_fields_subset_of_v1",
                    "remove fields not defined by v1: " + ", ".join(unknown))

    out: Dict[str, Any] = {"schema": SCHEMA_ID}
    for key in DESCRIPTOR_REQUIRED:
        value = descriptor.get(key)
        if not isinstance(value, str) or not value:
            return deny("MISSING_REQUIRED_FIELD", key + "_is_nonempty_string", "provide " + key)
        out[key] = value
    if out["work_class"] not in WORK_CLASSES:
        return deny("UNSUPPORTED_WORK_CLASS", "work_class_in_v1_enum",
                    "use one of: " + ", ".join(WORK_CLASSES))

    for key, default in DESCRIPTOR_DEFAULTS.items():
        value = descriptor.get(key, default)
        if isinstance(default, (list, dict)) and value is None:
            value = type(default)()
        out[key] = json.loads(canonical_json(value))

    for key in ("input_media", "output_media"):
        media = out[key]
        if not isinstance(media, list):
            return deny("INVALID_MEDIA_LIST", key + "_is_list", "provide " + key + " as a list")
        bad = [m for m in media if m not in MEDIA_TYPES]
        if bad:
            return deny("UNSUPPORTED_MEDIA_TYPE", key + "_in_v1_media_enum",
                        "use media types from: " + ", ".join(MEDIA_TYPES))
    for key in ("model", "required_tier"):
        if out[key] is not None and not isinstance(out[key], str):
            return deny("INVALID_FIELD_TYPE", key + "_is_string_or_null", "provide " + key + " as string or null")
    if out["entitlement_state"] not in ENTITLEMENT_STATES:
        return deny("INVALID_ENTITLEMENT_STATE", "entitlement_state_in_v1_enum",
                    "use one of: " + ", ".join(ENTITLEMENT_STATES))
    if out["routing_disposition"] not in ROUTING_DISPOSITIONS:
        return deny("INVALID_ROUTING_DISPOSITION", "routing_disposition_in_v1_enum",
                    "use one of: " + ", ".join(ROUTING_DISPOSITIONS))
    if not isinstance(out["execution_constraints"], dict):
        return deny("INVALID_FIELD_TYPE", "execution_constraints_is_object", "provide an object")
    _, nested_secrets = _strip_secrets(out["execution_constraints"])
    if nested_secrets:
        return deny("CREDENTIAL_MATERIAL_IN_DESCRIPTOR", "descriptor_contains_no_credentials",
                    "remove credential-like keys from execution_constraints")
    if out["evidence_return"] != "RETAINED_OBSERVATION_REQUIRED":
        return deny("INVALID_EVIDENCE_RETURN", "evidence_return == RETAINED_OBSERVATION_REQUIRED",
                    "set evidence_return to RETAINED_OBSERVATION_REQUIRED")
    if out["authority_effect"] != AUTHORITY_EFFECT:
        return deny("AUTHORITY_CLAIM_NOT_PERMITTED", "authority_effect == NONE",
                    "HCB descriptors are non-authorizing; set authority_effect to NONE")

    return ContractResult(
        operation=op,
        disposition=ALLOW,
        output=out,
        input_sha256=input_sha,
        evidence={"descriptor_sha256": sha256_of(out)},
    )


@dataclass(frozen=True)
class ProtocolMapping:
    """A recognized, versioned, non-network mapping from a source shape to an SDK input candidate."""

    protocol: str
    version: str
    media: Tuple[str, ...]
    prompt_field: str
    options_field: Optional[str]
    model_field: Optional[str]
    passthrough: Tuple[str, ...]
    derived_from: str
    required_values: Tuple[Tuple[str, Any], ...] = ()

    def spec(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "version": self.version,
            "mapping_version": MAPPING_VERSION,
            "media": list(self.media),
            "prompt_field": self.prompt_field,
            "options_field": self.options_field,
            "model_field": self.model_field,
            "passthrough": list(self.passthrough),
            "required_values": [list(rv) for rv in self.required_values],
            "derived_from": self.derived_from,
        }

    @property
    def sha256(self) -> str:
        return sha256_of(self.spec())


# Only shapes derivable from this repository's existing request structures.
RECOGNIZED_MAPPINGS: Tuple[ProtocolMapping, ...] = (
    ProtocolMapping(
        protocol="hcb.task",
        version="v1",
        media=("text",),
        prompt_field="prompt",
        options_field="options",
        model_field=None,
        passthrough=(),
        required_values=(("task_type", "text-generate"),),
        derived_from="api/app/tasks.py Task(task_type, prompt, options); providers.yaml capability text-generate",
    ),
    ProtocolMapping(
        protocol="ollama.generate",
        version="v1",
        media=("text",),
        prompt_field="prompt",
        options_field="options",
        model_field="model",
        passthrough=("stream",),
        derived_from="api/app/providers/ollama_text.py POST /api/generate payload {model, prompt, stream, options}",
    ),
)

_PROMPT_HINTS = ("prompt", "input", "text", "query", "message", "messages", "contents", "content")


class ProtocolAdapter:
    """Pure translator from recognized protocol envelopes to SDK input candidates.

    Envelope: {"protocol": str, "protocol_version": str, "media_type": str, "payload": object}.
    The adapter never performs I/O and never emits credential material.
    """

    def __init__(self, mappings: Tuple[ProtocolMapping, ...] = RECOGNIZED_MAPPINGS):
        self._mappings: Dict[str, ProtocolMapping] = {m.protocol: m for m in mappings}

    @property
    def recognized_protocols(self) -> List[str]:
        return sorted(self._mappings)

    def translate(self, envelope: Mapping[str, Any]) -> ContractResult:
        op = "translate"
        if not isinstance(envelope, Mapping) or not isinstance(envelope.get("payload"), Mapping):
            return _non_allow(
                op, FAIL_CLOSED, "MALFORMED_PROTOCOL_ENVELOPE", "envelope_has_object_payload",
                "submit {protocol, protocol_version, media_type, payload:{...}}",
                TRANSLATE_RETRY_ENTRYPOINT, "resubmit a well-formed envelope",
                input_sha256=sha256_of(envelope) if isinstance(envelope, Mapping) else None,
            )
        input_sha = sha256_of(dict(envelope))
        protocol = envelope.get("protocol")
        version = envelope.get("protocol_version")
        media = envelope.get("media_type", "text")
        payload = envelope["payload"]

        mapping = self._mappings.get(protocol) if isinstance(protocol, str) else None
        if mapping is None:
            return _non_allow(
                op, FAIL_CLOSED, "UNKNOWN_PROTOCOL", "protocol_in_recognized_mappings",
                "a reviewed, versioned mapping for this protocol vendored in hcb_contract "
                "(VENDOR_MANIFEST digest); the candidate mapping below is evidence only",
                SDK_RETRY_ENTRYPOINT,
                "after a reviewed mapping is vendored; nothing is executed or installed",
                input_sha256=input_sha,
                evidence={
                    "recognized_protocols": self.recognized_protocols,
                    "candidate_mapping": self._candidate_mapping(protocol, payload),
                },
            )

        evidence_base = {"mapping_protocol": mapping.protocol, "mapping_version": MAPPING_VERSION,
                         "mapping_sha256": mapping.sha256}
        if version != mapping.version:
            return _non_allow(
                op, DENY, "PROTOCOL_VERSION_MISMATCH",
                "protocol_version == " + mapping.version,
                "re-express the input as " + mapping.protocol + " " + mapping.version,
                TRANSLATE_RETRY_ENTRYPOINT, "resubmit with a supported protocol_version",
                input_sha256=input_sha, evidence=dict(evidence_base, supported_version=mapping.version),
            )
        if media not in mapping.media:
            return _non_allow(
                op, DENY, "UNSUPPORTED_MEDIA_TYPE", "media_type_in_mapping_media",
                "submit media_type in " + ", ".join(mapping.media),
                TRANSLATE_RETRY_ENTRYPOINT, "resubmit with a supported media_type",
                input_sha256=input_sha, evidence=dict(evidence_base, supported_media=list(mapping.media)),
            )
        for key, expected in mapping.required_values:
            if payload.get(key) != expected:
                return _non_allow(
                    op, DENY, "UNSUPPORTED_TASK_SHAPE", key + " == " + repr(expected),
                    "set payload." + key + " to " + repr(expected),
                    TRANSLATE_RETRY_ENTRYPOINT, "resubmit a supported task shape",
                    input_sha256=input_sha, evidence=evidence_base,
                )
        prompt = payload.get(mapping.prompt_field)
        if not isinstance(prompt, str) or not prompt.strip():
            return _non_allow(
                op, DENY, "MISSING_PROMPT", mapping.prompt_field + "_is_nonempty_string",
                "provide payload." + mapping.prompt_field,
                TRANSLATE_RETRY_ENTRYPOINT, "resubmit with a prompt",
                input_sha256=input_sha, evidence=evidence_base,
            )

        options: Dict[str, Any] = {}
        field_map = [{"from": "payload." + mapping.prompt_field, "to": "prompt"}]
        if mapping.options_field:
            raw = payload.get(mapping.options_field) or {}
            if not isinstance(raw, Mapping):
                return _non_allow(
                    op, DENY, "INVALID_OPTIONS", mapping.options_field + "_is_object",
                    "provide payload." + mapping.options_field + " as an object",
                    TRANSLATE_RETRY_ENTRYPOINT, "resubmit with object options",
                    input_sha256=input_sha, evidence=evidence_base,
                )
            options = dict(raw)
            field_map.append({"from": "payload." + mapping.options_field, "to": "options"})
        for key in mapping.passthrough:
            if key in payload:
                options[key] = payload[key]
                field_map.append({"from": "payload." + key, "to": "options." + key})
        options, redacted = _strip_secrets(options)

        candidate: Dict[str, Any] = {
            "schema": SDK_INPUT_CANDIDATE_SCHEMA_ID,
            "capability_id": "text-generate",
            "work_class": "text",
            "input_media": [media],
            "prompt": prompt,
            "options": json.loads(canonical_json(options)),
            "target_ref": "bridge:hybrid-collab",
            "authority_effect": AUTHORITY_EFFECT,
        }
        if mapping.model_field:
            model = payload.get(mapping.model_field)
            if isinstance(model, str) and model:
                candidate["model"] = model
                field_map.append({"from": "payload." + mapping.model_field, "to": "model"})

        return ContractResult(
            operation=op,
            disposition=ALLOW,
            output=candidate,
            input_sha256=input_sha,
            evidence=dict(
                evidence_base,
                transformation={
                    "field_map": field_map,
                    "redacted_field_count": redacted,
                    "dropped_payload_fields": sorted(
                        k for k in payload
                        if not is_secret_like_key(k)
                        and k not in {mapping.prompt_field, mapping.options_field, mapping.model_field}
                        and k not in mapping.passthrough
                        and k not in dict(mapping.required_values)
                    ),
                },
                output_sha256=sha256_of(candidate),
            ),
        )

    @staticmethod
    def _candidate_mapping(protocol: Any, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Describe a novel shape from non-secret key metadata only; never selectable."""
        observed = {
            str(k): type(v).__name__
            for k, v in sorted(payload.items(), key=lambda kv: str(kv[0]))
            if not is_secret_like_key(k)
        }
        prompt_guess = next((k for k in _PROMPT_HINTS if k in observed), None)
        candidate = {
            "source_protocol": protocol if isinstance(protocol, str) else None,
            "observed_fields": observed,
            "proposed_prompt_field": prompt_guess,
            "mapping_version": MAPPING_VERSION,
            "selectable": False,
            "authority_effect": AUTHORITY_EFFECT,
        }
        candidate["candidate_sha256"] = sha256_of(candidate)
        return candidate
