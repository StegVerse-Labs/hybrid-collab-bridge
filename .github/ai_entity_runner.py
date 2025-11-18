import os
import json
import textwrap
from pathlib import Path

import requests


MODELS_ENDPOINT = "https://models.github.ai/inference/chat/completions"


def gather_context() -> str:
    """
    Collect a small, targeted slice of repo context for the model:
    - stegverse_connectivity.md
    - workflows under .github/workflows/
    - README files
    """
    root = Path(".").resolve()
    parts = []

    # Connectivity spec
    conn = root / "stegverse_connectivity.md"
    if conn.exists():
        try:
            parts.append(
                "# File: stegverse_connectivity.md\n"
                + conn.read_text(errors="ignore")[:4000]
            )
        except Exception:
            pass

    # Workflows
    wf_root = root / ".github" / "workflows"
    if wf_root.exists():
        for wf in sorted(wf_root.glob("*.yml")):
            try:
                txt = wf.read_text(errors="ignore")
                parts.append(f"# File: .github/workflows/{wf.name}\n{txt[:3000]}")
            except Exception:
                pass

    # README files
    for readme in [root / "README.md", root / "README-HCB.md"]:
        if readme.exists():
            try:
                parts.append(
                    f"# File: {readme.name}\n"
                    + readme.read_text(errors="ignore")[:3000]
                )
            except Exception:
                pass

    return "\n\n---\n\n".join(parts)


def call_github_model(system_prompt: str, user_prompt: str, gh_token: str) -> str:
    """
    Call GitHub Models chat completions API using the provided GH token.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {gh_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 900,
        "temperature": 0.2,
    }

    resp = requests.post(MODELS_ENDPOINT, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(data, indent=2)


def main():
    instructions = os.environ.get("INSTRUCTIONS", "").strip()
    if not instructions:
        instructions = (
            "Audit and improve this repo's connectivity based on "
            "stegverse_connectivity.md."
        )

    gh_token = os.environ.get("GH_TOKEN")
    if not gh_token:
        raise SystemExit("Missing GH_TOKEN in environment for GitHub Models call.")

    repo = os.environ.get("REPO", "(unknown repo)")
    repo_context = gather_context()

    system_prompt = (
        'You are "StegVerse-AI-001", operating INSIDE the Hybrid-Collab-Bridge '
        "repository as a connectivity-focused maintainer.\n\n"
        "Guardian rules:\n"
        "- Follow StegVerse Guardian principles: security, transparency, "
        "verifiability, non-abuse.\n"
        "- Work ONLY within this repository.\n"
        "- Never expose or invent secrets, tokens, or keys.\n"
        "- Prefer small, safe, incremental edits over large refactors.\n"
        "- Focus on workflows, naming consistency, and connectivity to other "
        "StegVerse modules.\n"
        "- Treat Rigel and human maintainers as final authority.\n"
    )

    user_prompt = textwrap.dedent(
        f"""
        Repository: {repo}
        Task from human:
        {instructions}

        Your mission:
        - Focus ONLY on this repo (Hybrid-Collab-Bridge).
        - Use stegverse_connectivity.md as the source of truth for how this repo
          should connect to:
          - StegVerse/StegCore
          - StegVerse/tv
          - StegVerse/stegverse-SCW
        - Identify problems in:
          - .github/workflows/*.yml (triggers, dispatch types, repo names)
          - README / docs that describe connectivity
        - Propose concrete changes (edits to specific files) to repair or improve
          connectivity.
        - Return your answer as:
          1) Summary
          2) Findings (bullet points)
          3) Suggested patches (show file paths and fenced code blocks)

        Current repo snapshot (partial, truncated for length):

        {repo_context}
        """
    )

    print("=== Calling GitHub Models for StegVerse connectivity entity ===")
    answer = call_github_model(system_prompt, user_prompt, gh_token=gh_token)

    print("\n===== StegVerse-AI-001 plan / suggestions =====\n")
    print(answer)
    print("\n===== END AI OUTPUT =====\n")

    # NOTE:
    # For now, we only PRINT the plan. We are not auto-editing files yet.
    # If you (or a later helper) modify files in this job, the workflow's
    # commit step will detect and commit those changes.


if __name__ == "__main__":
    main()
