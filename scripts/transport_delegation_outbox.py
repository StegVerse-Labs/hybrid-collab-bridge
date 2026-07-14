#!/usr/bin/env python3
"""Transport delegation outbox records through an explicitly authorized token.

Without STEGVERSE_TRANSPORT_TOKEN this script records BLOCKED_EXTERNAL_AUTHORITY
and exits cleanly. It never invents credentials or broadens destination scope.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API = "https://api.github.com"
DEFAULT_DESTINATION_REPO = "StegVerse-Labs/Ecosystem-Delegation"
DEFAULT_DESTINATION_DIR = "inbox/hybrid-collab-bridge"


def _request(url: str, token: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "StegVerse-governed-transport",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload) if payload else {}


def _existing_sha(repo: str, path: str, token: str) -> str | None:
    url = f"{API}/repos/{repo}/contents/{path}"
    try:
        return _request(url, token).get("sha")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def transport(
    outbox: Path,
    state_path: Path,
    token: str | None,
    destination_repo: str = DEFAULT_DESTINATION_REPO,
    destination_dir: str = DEFAULT_DESTINATION_DIR,
) -> dict[str, Any]:
    records = sorted(outbox.glob("*.json"))
    transmitted: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []

    if not token:
        state = {
            "schema_version": "1.0",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "status": "BLOCKED_EXTERNAL_AUTHORITY",
            "source_repository": "StegVerse-Labs/hybrid-collab-bridge",
            "destination_repository": destination_repo,
            "pending_count": len(records),
            "transmitted": [],
            "failed": [],
            "transport_authority_present": False,
            "manual_action_required": False,
        }
    else:
        for source in records:
            destination_path = f"{destination_dir.rstrip('/')}/{source.name}"
            try:
                content = source.read_bytes()
                body: dict[str, Any] = {
                    "message": f"Receive governed delegation candidate {source.stem}",
                    "content": base64.b64encode(content).decode("ascii"),
                    "branch": "main",
                }
                sha = _existing_sha(destination_repo, destination_path, token)
                if sha:
                    body["sha"] = sha
                result = _request(
                    f"{API}/repos/{destination_repo}/contents/{destination_path}",
                    token,
                    method="PUT",
                    body=body,
                )
                transmitted.append({
                    "source": str(source),
                    "destination": f"{destination_repo}:{destination_path}",
                    "commit_sha": str(result.get("commit", {}).get("sha") or ""),
                })
            except Exception as exc:
                failed.append({"source": str(source), "error": f"{type(exc).__name__}: {exc}"})
        state = {
            "schema_version": "1.0",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "status": "TRANSPORT_COMPLETE" if not failed else "TRANSPORT_PARTIAL_FAILURE",
            "source_repository": "StegVerse-Labs/hybrid-collab-bridge",
            "destination_repository": destination_repo,
            "pending_count": len(records),
            "transmitted": transmitted,
            "failed": failed,
            "transport_authority_present": True,
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
        os.getenv("STEGVERSE_TRANSPORT_TOKEN"),
        args.destination_repo,
        args.destination_dir,
    )
    print(json.dumps(state, sort_keys=True))
    return 0 if state["status"] in {"BLOCKED_EXTERNAL_AUTHORITY", "TRANSPORT_COMPLETE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
