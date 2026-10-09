"""Six-field non-ALLOW dispositions for provider results.

Every provider result that is not an ALLOW (successful ``text``) carries the
conformance fields required by StegVerse-org/.github
docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md: failure_code,
failed_predicate, required_evidence_or_repair, retry_entrypoint,
owning_existing_goal and next_attempt. The legacy ``state`` and ``error`` keys
are kept for existing callers. Stdlib only; no authority is conferred.
"""
from typing import Any, Dict

OWNING_EXISTING_GOAL = "HCB-VERSIONED-CONTRACT-038"
SDK_RETRY_ENTRYPOINT = "StegVerse-SDK manifest submission -> StegVerse-org/.github -> Interlock/InTr"
PROVIDER_RUN_RETRY_ENTRYPOINT = "POST /v1/run with a supported task_type"

SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)

FAIL_CLOSED = "FAIL_CLOSED"
DENY = "DENY"


def provider_non_allow(
    *,
    provider: str,
    provider_type: str,
    failure_code: str,
    failed_predicate: str,
    required_evidence_or_repair: str,
    retry_entrypoint: str,
    next_attempt: str,
    disposition: str = FAIL_CLOSED,
    state: str = "BLOCKED",
    error: str = "",
    **extra: Any,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "state": state,
        "disposition": disposition,
        "error": error or failure_code,
        "provider": provider,
        "provider_type": provider_type,
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": required_evidence_or_repair,
        "retry_entrypoint": retry_entrypoint,
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": next_attempt,
        "provider_execution_performed": False,
        "authority_effect": False,
    }
    result.update(extra)
    return result


def unsupported_task(provider: Any, task_type: str) -> Dict[str, Any]:
    return provider_non_allow(
        provider=provider.name,
        provider_type=provider.type,
        disposition=DENY,
        state="DENIED",
        error="unsupported task",
        failure_code="UNSUPPORTED_TASK_TYPE",
        failed_predicate=f"task_type in {list(provider.capabilities)!r} (got {task_type!r})",
        required_evidence_or_repair="resubmit with a task_type this provider declares",
        retry_entrypoint=PROVIDER_RUN_RETRY_ENTRYPOINT,
        next_attempt="resubmit with a supported task_type",
    )


def admitted_route_required(provider: Any, reason: str) -> Dict[str, Any]:
    return provider_non_allow(
        provider=provider.name,
        provider_type=provider.type,
        error=reason,
        failure_code=reason,
        failed_predicate="hcb_provider_adapter_holds_no_credentials_and_performs_no_provider_call",
        required_evidence_or_repair=(
            "route the provider operation through the LLM-adapter external_llm_connection "
            "primitive (TV/TVC-held credentials, Interlock/InTr admission); HCB is not a provider hop"
        ),
        retry_entrypoint=SDK_RETRY_ENTRYPOINT,
        next_attempt="immediately via SDK manifest submission; nothing in HCB waits for a TV/TVC route",
        credential_material_present=False,
    )


def provider_unreachable(provider: Any, detail: str, endpoint: str) -> Dict[str, Any]:
    return provider_non_allow(
        provider=provider.name,
        provider_type=provider.type,
        error=detail,
        failure_code="PROVIDER_ENDPOINT_UNAVAILABLE",
        failed_predicate=f"provider_endpoint_responds ({endpoint})",
        required_evidence_or_repair=(
            "configure a reachable local endpoint or select another enabled provider; "
            "the bridge does not wait for the endpoint"
        ),
        retry_entrypoint=PROVIDER_RUN_RETRY_ENTRYPOINT,
        next_attempt="next /v1/run request",
    )
