"""Hybrid-Collab-Bridge local AI entity runner.

This runner intentionally avoids fetching remote StegTVC configuration during
the connectivity self-check. The previous failure boundary was a 404 while
fetching config before the entity could produce a useful artifact.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from stegtvc_client import stegtvc_resolve


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    repo = os.environ.get("REPO", "")
    instructions = os.environ.get("INSTRUCTIONS", "")
    system_prompt = os.environ.get("SYSTEM_PROMPT", "")
    user_prompt = os.environ.get("USER_PROMPT", "")

    print("=== Hybrid-Collab-Bridge AI Entity Runner ===")
    print("🔎 Resolving model via local StegTVC compatibility client...")

    result: Dict[str, Any] = stegtvc_resolve(
        use_case="connectivity-entity",
        module="hybrid-collab-bridge",
        importance="normal",
        repo=repo,
    )

    print("✅ StegTVC local resolution completed.")
    print(json.dumps(result, indent=2, sort_keys=True))

    root = Path.cwd()
    source_doc = _read_optional(root / "stegverse_connectivity.md")

    report = {
        "status": "ok",
        "repo": repo,
        "instructions": instructions,
        "system_prompt_present": bool(system_prompt),
        "user_prompt_present": bool(user_prompt),
        "connectivity_doc_present": bool(source_doc.strip()),
        "stegtvc_resolution": result,
    }

    output_dir = root / "brain_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "connectivity_entity_result.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"✅ Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
