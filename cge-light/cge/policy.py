from __future__ import annotations


def evaluate_bcat(ingest_result: dict) -> dict:
    payload = ingest_result.get("payload", {})
    observability = 0.80 if payload else 0.20
    context_stability = 0.75
    trust_continuity = 0.70
    authority_clarity = 0.70
    reversibility_margin = 0.90
    risk = 0.20
    return {
        "observability": observability,
        "context_stability": context_stability,
        "trust_continuity": trust_continuity,
        "authority_clarity": authority_clarity,
        "reversibility_margin": reversibility_margin,
        "risk": risk,
    }


def evaluate_gcat(bcat: dict) -> dict:
    g = bcat["authority_clarity"]
    c = bcat["context_stability"]
    a = 1.0 - bcat["reversibility_margin"]
    t = max(0.0, min(1.0, bcat["risk"]))
    total = g + c + a + t
    if total == 0:
        total = 1.0
    return {
        "g": g / total,
        "c": c / total,
        "a": a / total,
        "t": t / total,
    }
