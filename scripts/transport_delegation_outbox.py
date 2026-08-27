#!/usr/bin/env python3
"""Emit a non-secret delegation transport observation.

Hybrid-Collab-Bridge is not a credential-bearing transport authority. Actual
cross-repository transport must be performed by an already-admitted TV/TVC
capability and return only bounded non-secret result/evidence to this repo.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DESTINATION_REPO = "StegVerse-Labs/Ecosystem-Delegation"
DEFAULT_DESTINATION_DIR = "inbox/hybrid-collab-bridge"


def transport(
    outbox: Path,
    state_path: Path,
    token: str | None = None,
    destination_repo: str = DEFAULT_DESTINATION_REPO,
    destination_dir: str = DEFAULT_DESTINATION_DIR,
) -> dict[str, Any]:
    """Record the fail-closed TV/TVC transport boundary.

    The token argument is retained only for backwards-compatible callers. It is
    never consumed, transmitted, logged, or used to authorize transport.
    """
    records = sorted(outbox.glob("*.json"))
    state = {
        "schema_version": "2.0",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "status": "TVC_ADMITTED_TRANSPORT_REQUIRED",
        "source_repository": "StegVerse-Labs/hybrid-collab-bridge",
        "destination_repository": destination_repo,
        "destination_directory": destination_dir,
        "pending_count": len(records),
        "transmitted": [],
        "failed": [],
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "consumer_token_accepted": False,
        "transport_performed": False,
        "github_actions_role": "VALIDATION_TRANSPORT_ONLY",
        "authority_effect": "NONE",
        "manual_action_required": False,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outbox", type=Path, default=Path("outbox/ecosystem-delegation"))
    parser.add_argument("--state", type=Path, default=Path("state/delegation_transport.json"))
    parser.add_argument("--destination-repo", default=DEFAULT_DESTINATION_REPO)
    parser.add_argument("--destination-dir", default=DEFAULT_DESTINATION_DIR)
    args = parser.parse_args()
    state = transport(
        args.outbox,
        args.state,
        None,
        args.destination_repo,
        args.destination_dir,
    )
    print(json.dumps(state, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
