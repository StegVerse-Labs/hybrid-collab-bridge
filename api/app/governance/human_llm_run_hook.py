"""Automatic governed Human–LLM assessment attachment for /v1/run.

The hook is deliberately fail-closed. A caller may supply a complete
`interoperability_assessment` object in the run request. When none is supplied,
the bridge emits an automatically constructed baseline whose semantic tests are
INDETERMINATE because fluent output alone cannot prove preserved meaning,
comprehension, or evaluative control.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from .human_llm_interoperability import AssessmentSubmission, REQUIRED_TESTS, submit_assessment

_INSTALLED_ATTR = "_human_llm_run_hook_installed"


def _baseline_assessment(request_payload: dict[str, Any], run_payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(run_payload.get("chain_id") or request_payload.get("slug") or uuid4().hex)
    consequence = str(request_payload.get("claim_consequence", "low")).lower()
    critical = {
        "meaning_preservation",
        "boundary_control",
        "audit_gap_control",
        "review_comprehension",
    }
    tests = {
        name: {
            "status": "INDETERMINATE",
            "score": 0.0,
            "critical": name in critical,
            "evidence": ["Automatically attached after /v1/run; no independent test evidence was supplied."],
        }
        for name in REQUIRED_TESTS
    }
    return {
        "assessment_id": f"auto-{uuid4().hex}",
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claim_consequence": consequence if consequence in {"low", "moderate", "high", "critical"} else "low",
        "tests": tests,
        "review": {
            "human_present": bool(request_payload.get("human_gate", False)),
            "comprehension_demonstrated": False,
            "objections_considered": False,
        },
        "overall_outcome": "INDETERMINATE",
        "error_attribution": [],
        "notes": "Automatic evidence-bounded baseline; independent interoperability evidence was not supplied.",
    }


def assessment_for_run(request_payload: dict[str, Any], run_payload: dict[str, Any]) -> dict[str, Any]:
    supplied = request_payload.get("interoperability_assessment")
    if isinstance(supplied, dict):
        return json.loads(json.dumps(supplied))
    return _baseline_assessment(request_payload, run_payload)


class HumanLLMRunAssessmentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != "POST" or request.url.path != "/v1/run":
            return await call_next(request)

        raw_request = await request.body()
        try:
            request_payload = json.loads(raw_request or b"{}")
        except json.JSONDecodeError:
            request_payload = {}

        response = await call_next(request)
        chunks = [chunk async for chunk in response.body_iterator]
        body = b"".join(chunks)
        rebuilt = Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=response.background,
        )
        if response.status_code >= 400:
            return rebuilt
        try:
            run_payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            return rebuilt
        session_path = run_payload.get("session_path")
        if not isinstance(session_path, str) or not session_path:
            return rebuilt

        assessment = assessment_for_run(request_payload, run_payload)
        try:
            result = await submit_assessment(
                AssessmentSubmission(
                    session_path=session_path,
                    assessment=assessment,
                    reviewer_action="automatic_post_run_attachment",
                    reviewer_entity_id="bridge-human-llm-assessor",
                ),
                x_admin_token=request.headers.get("x-admin-token"),
            )
            run_payload["interoperability"] = result.model_dump()
        except Exception as exc:
            run_payload["interoperability"] = {
                "outcome": "INDETERMINATE",
                "admission_decision": "deny",
                "publication_allowed": False,
                "errors": [f"automatic assessment attachment failed: {type(exc).__name__}: {exc}"],
            }
        return Response(
            content=json.dumps(run_payload),
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
            media_type="application/json",
            background=response.background,
        )


def install_run_assessment_hook(app: FastAPI) -> bool:
    if getattr(app.state, _INSTALLED_ATTR, False):
        return False
    app.add_middleware(HumanLLMRunAssessmentMiddleware)
    setattr(app.state, _INSTALLED_ATTR, True)
    return True
