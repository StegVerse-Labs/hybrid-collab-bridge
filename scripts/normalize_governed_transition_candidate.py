#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

from verify_hps_bridge_route import decide

ORIGIN_MAP = {
    "SDK_INPUT": "SDK",
    "LLM_ADAPTER_INPUT": "LLM_ADAPTER",
    "SITE_INPUT": "SITE",
    "EXTERNAL_ADAPTER": "EXTERNAL_ADAPTER",
    "MANUAL_REVIEW": "MANUAL_REVIEW",
}


def fail(message: str) -> int:
    print(f"GOVERNED TRANSITION NORMALIZATION: FAIL - {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 4:
        return fail("usage: normalize_governed_transition_candidate.py <candidate.json> <route.json> <output.json>")

    candidate_path = Path(sys.argv[1])
    route_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    if not candidate_path.exists() or not route_path.exists():
        return fail("candidate or route input missing")

    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    route = json.loads(route_path.read_text(encoding="utf-8"))

    if candidate.get("record_type") != "governed_transition_relationship":
        return fail("candidate record_type mismatch")
    if candidate.get("lifecycle_state") != "DECLARED":
        return fail("candidate must enter bridge as DECLARED")

    origin_class = candidate.get("origin", {}).get("origin_class")
    expected_route_origin = ORIGIN_MAP.get(origin_class)
    if expected_route_origin is None:
        return fail(f"unsupported origin_class: {origin_class}")
    if route.get("origin") != expected_route_origin:
        return fail("candidate origin and HPS route origin do not match")

    result = decide(route)
    if not result.ok:
        return fail("; ".join(result.errors))

    normalized = deepcopy(candidate)
    normalized["lifecycle_state"] = {
        "ALLOW_NEXT_BOUNDARY": "READY",
        "REVIEW": "VERIFICATION_REQUIRED",
        "DENY": "BLOCKED",
        "FAIL_CLOSED": "FAIL_CLOSED",
    }[result.decision]
    normalized["relationships"]["target_ref"] = "repository:StegVerse-Labs/Ecosystem-Delegation"
    normalized["governance"]["evidence_refs"] = list(dict.fromkeys(
        normalized["governance"]["evidence_refs"] + [
            f"bridge-route:{route['route_id']}",
            f"bridge-decision:{result.decision}",
        ]
    ))
    normalized["governance"]["admissibility_result"] = "PENDING"
    normalized["governance"]["commit_time_validity"] = "PENDING"
    normalized["execution"] = {
        "action_ref": None,
        "verification_ref": f"bridge-verification:{route['route_id']}",
        "resulting_state_ref": None,
    }
    normalized["continuity"]["final_receipt_id"] = None
    normalized["continuity"]["master_record_ref"] = None
    normalized["continuity"]["master_record_status"] = "NOT_YET_SUBMITTED"
    normalized["continuity"]["reconstruction_status"] = "NOT_YET_CHECKED"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    print(
        "GOVERNED TRANSITION NORMALIZATION: PASS "
        f"transition_id={normalized['transition_id']} decision={result.decision}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
