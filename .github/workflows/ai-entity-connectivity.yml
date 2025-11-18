import os
import sys

# Ensure Python can import helper modules from .github directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)
"""
AI Entity Runner for Hybrid-Collab-Bridge
Now routed through StegTVC Core v1.0
"""

import os
import json
import sys
import urllib.request

# Use our new helper
from stegtvc_client import stegtvc_resolve

def call_github_models(model: str, system: str, user: str, gh_token: str):
    """Direct call to GitHub Models."""
    url = "https://models.github.ai/inference/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 900,
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gh_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        txt = resp.read().decode("utf-8")
        return json.loads(txt)


def main():
    print("=== Hybrid-Collab-Bridge AI Entity Runner ===")

    gh_token = os.getenv("GH_TOKEN")
    if not gh_token:
        print("❌ GH_TOKEN is missing.")
        sys.exit(1)

    # -------------------------------------------------------------------
    # 1. Resolve provider/model from StegTVC
    # -------------------------------------------------------------------
    try:
        print("🔍 Asking StegTVC which provider/model to use...")
        resolved = stegtvc_resolve(
            use_case="code-review",
            module="hybrid-collab-bridge",
            importance="normal",
        )
    except Exception as e:
        print(f"❌ StegTVC resolution failed: {e}")
        sys.exit(1)

    provider = resolved["provider"]
    model = provider["model"]
    print(f"📡 StegTVC selected model: {model}")

    # -------------------------------------------------------------------
    # 2. Load AI prompts from environment
    # -------------------------------------------------------------------
    system_prompt = os.getenv("SYSTEM_PROMPT", "You are StegVerse-AI-001.")
    user_prompt = os.getenv("USER_PROMPT", "No specific user instructions.")

    # -------------------------------------------------------------------
    # 3. Call GitHub Models
    # -------------------------------------------------------------------
    try:
        print("🤖 Calling GitHub Models...")
        response = call_github_models(
            model=model,
            system=system_prompt,
            user=user_prompt,
            gh_token=gh_token,
        )
    except Exception as e:
        print(f"❌ GitHub Models error: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------
    # 4. Output
    # -------------------------------------------------------------------
    try:
        ai_text = response["choices"][0]["message"]["content"]
    except Exception:
        ai_text = json.dumps(response)

    print("\n===== AI OUTPUT =====")
    print(ai_text)
    print("=====================")


if __name__ == "__main__":
    main()
