"""
StegTVC Client - PUBLIC SAFE VERSION
Automatically resolves provider/model for AI entity runners.
"""

import json
import urllib.request


TVC_URL = "https://raw.githubusercontent.com/StegVerse-Labs/StegTVC/main/config/resolution_rules.json"


def stegtvc_resolve(use_case: str, module: str, importance: str = "normal"):
    """
    Fetches the StegTVC configuration JSON (public) and selects the model.
    """

    try:
        with urllib.request.urlopen(TVC_URL, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch StegTVC config: {e}")

    # Resolve rules
    rules = data.get("rules", {})
    if use_case not in rules:
        raise RuntimeError(f"No rule found for use_case '{use_case}'")

    entry = rules[use_case]
    provider = entry.get("provider", {})
    model = provider.get("model")

    if not model:
        raise RuntimeError("Model not defined in StegTVC config.")

    return {
        "provider": provider,
        "model": model,
        "module": module,
        "importance": importance,
    }
