import os
import sys
import json
import urllib.request

# Allow importing helper files from .github/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from stegtvc_client import stegtvc_resolve


def call_github_models(model: str, system: str, user: str, gh_token: str):
    """Direct call to GitHub Models API."""
    url = "https://models.github.ai/inference/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 800,
        "temperature": 0.25,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gh_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=== Hybrid-Collab-Bridge AI Entity Runner ===")

    gh_token = os.getenv("GH_TOKEN")
    if not gh_token:
        print("❌ GH_TOKEN missing")
        sys.exit(1)

    # Step 1 — Resolve provider via StegTVC
    try:
        print("🔍 Resolving model via StegTVC...")
        resolved = stegtvc_resolve(
            use_case="code-review",
            module="hybrid-collab-bridge",
        )
    except Exception as e:
        print(f"❌ StegTVC resolution failed: {e}")
        sys.exit(1)

    model = resolved["model"]
    print(f"📡 Using model: {model}")

    # Step 2 — Load prompts
    system_prompt = os.getenv("SYSTEM_PROMPT", "You are StegVerse-AI-Entity.")
    user_prompt = os.getenv("USER_PROMPT", "No instructions provided.")

    # Step 3 — Call GitHub Models
    try:
        print("🤖 Calling GitHub Models...")
        response = call_github_models(model, system_prompt, user_prompt, gh_token)
    except Exception as e:
        print(f"❌ GitHub Models error: {e}")
        sys.exit(1)

    # Step 4 — Print output
    try:
        msg = response["choices"][0]["message"]["content"]
        print("\n===== AI OUTPUT =====")
        print(msg)
        print("=====================\n")
    except Exception:
        print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
