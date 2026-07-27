"""Standalone FastAPI entry point for governed style experiments.

Deploy as: uvicorn api.app.style_api:app
"""
from fastapi import FastAPI

from .governance.style_experiments import router

app = FastAPI(
    title="Hybrid Collab Bridge Style Experiments",
    version="1.0.0",
    description=(
        "Governed accommodation measurement. Results describe observed feature "
        "convergence and never establish verified model origin."
    ),
)
app.include_router(router)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "style-experiments",
        "maximum_claim": "observed_feature_convergence",
        "origin_attribution": False,
    }
