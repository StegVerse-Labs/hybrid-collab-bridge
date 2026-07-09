#!/usr/bin/env python3
"""Verify HPS bridge route examples.

The bridge normalizes sibling input nests into a common route state without
turning SDK, LLM-adapter, Site, or external inputs into execution authority.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_TOP = {
    "route_type",
    "route_id",
    "origin",
    "requested_capability",
    "heartbeat_result",
    "standing_class",
    "standing_required",
    "capability_window_state",
    "supports",
    "expiration_triggers",
    "expected_bridge_decision",
}

REQUIRED_SUPPORTS = {
    "authority_valid",
    "policy_current",
    "delegation_current",
    "evidence_fresh",
    "coordinate_valid",
    "reconstruction_available",
}

VALID_DECISIONS = {"ALLOW_NEXT_BOUNDARY", "DENY", "REVIEW", "FAIL_CLOSED"}


@dataclass(frozen=True)
class BridgeResult:
    ok: bool
    decision: str
    errors: list[str]


def load_route(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("route root must be a JSON object")
    return data


def standing_satisfies(actual: str, required: str) -> bool:
    order = {"FAILED": 0, "DEGRADED": 1, "RESTORED": 2}
    return order.get(actual, -1) >= order.get(required, 99)


def decide(route: dict[str, Any]) -> BridgeResult:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP - set(route.keys()))
    for key in missing:
        errors.append(f"missing required field: {key}")
    if errors:
        return BridgeResult(False, "FAIL_CLOSED", errors)

    if route.get("route_type") != "hps_bridge_route":
        errors.append("route_type must be hps_bridge_route")

    supports = route.get("supports", {})
    if not isinstance(supports, dict):
        errors.append("supports must be an object")
        supports = {}
    for key in sorted(REQUIRED_SUPPORTS - set(supports.keys())):
        errors.append(f"missing required support: {key}")

    expiration_triggers = route.get("expiration_triggers", [])
    if not isinstance(expiration_triggers, list):
        errors.append("expiration_triggers must be a list")
        expiration_triggers = []

    if route.get("expected_bridge_decision") not in VALID_DECISIONS:
        errors.append("expected_bridge_decision is not recognized")

    heartbeat = route.get("heartbeat_result")
    standing_class = str(route.get("standing_class"))
    standing_required = str(route.get("standing_required"))
    window_state = route.get("capability_window_state")

    if heartbeat in {None, "UNKNOWN", "FAIL_CLOSED", "FAIL-CLOSED"}:
        decision = "FAIL_CLOSED"
    elif standing_class == "FAILED":
        decision = "FAIL_CLOSED"
    elif supports.get("reconstruction_available") is not True:
        decision = "FAIL_CLOSED"
    elif supports.get("coordinate_valid") is not True:
        decision = "FAIL_CLOSED"
    elif supports.get("authority_valid") is not True:
        decision = "FAIL_CLOSED"
    elif window_state == "REVIEW":
        decision = "REVIEW"
    elif window_state in {"CLOSED", "EXPIRED"}:
        decision = "DENY"
    elif expiration_triggers:
        decision = "DENY"
    elif heartbeat != "PASS":
        decision = "DENY"
    elif not standing_satisfies(standing_class, standing_required):
        decision = "DENY"
    elif any(supports.get(field) is not True for field in REQUIRED_SUPPORTS):
        decision = "DENY"
    else:
        decision = "ALLOW_NEXT_BOUNDARY"

    expected = route.get("expected_bridge_decision")
    if expected in VALID_DECISIONS and expected != decision:
        errors.append(f"expected_bridge_decision {expected} does not match actual decision {decision}")

    return BridgeResult(not errors, decision, errors)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: verify_hps_bridge_route.py <route.json>", file=sys.stderr)
        return 2
    try:
        result = decide(load_route(Path(argv[1])))
    except Exception as exc:
        print(f"decision: FAIL_CLOSED")
        print(f"- could not read route: {exc}")
        return 1

    print(f"decision: {result.decision}")
    for error in result.errors:
        print(f"- {error}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
