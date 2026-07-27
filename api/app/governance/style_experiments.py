"""Runtime API for governed human-LLM style accommodation experiments."""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/interoperability/style-experiments", tags=["style-experiments"])

WORD_RE = re.compile(r"[A-Za-z0-9']+")
FEATURES = (
    "mean_word_length",
    "mean_sentence_length",
    "type_token_ratio",
    "punctuation_density",
    "newline_density",
    "question_density",
    "colon_density",
    "dash_density",
)


class AccommodationExperimentRequest(BaseModel):
    experiment_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    human_baseline: str = Field(min_length=1)
    model_baseline: str = Field(min_length=1)
    human_revised: str = Field(min_length=1)
    model_followup: str = Field(min_length=1)
    minimum_identity_retention: float = Field(default=0.65, ge=0.0, le=1.0)


class AccommodationMetrics(BaseModel):
    initial_cross_distance: float
    final_cross_distance: float
    cross_convergence: float
    human_shift: float
    model_shift: float
    human_identity_retention: float
    model_style_retention: float


class AccommodationExperimentReport(BaseModel):
    experiment_id: str
    status: Literal["PASS"] = "PASS"
    determination: Literal[
        "bounded_accommodation_observed",
        "convergence_with_identity_loss",
        "no_accommodation_observed",
    ]
    metrics: AccommodationMetrics
    governance: dict[str, object]


def _root() -> Path:
    path = Path(os.getenv("HCB_STYLE_EXPERIMENT_ROOT", "runtime/style-experiments"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _features(text: str) -> dict[str, float]:
    words = WORD_RE.findall(text)
    sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
    chars = max(len(text), 1)
    tokens = max(len(words), 1)
    return {
        "mean_word_length": sum(map(len, words)) / tokens,
        "mean_sentence_length": len(words) / max(len(sentences), 1),
        "type_token_ratio": len({word.lower() for word in words}) / tokens,
        "punctuation_density": sum(1 for char in text if char in ",.;:!?—-") / chars,
        "newline_density": text.count("\n") / chars,
        "question_density": text.count("?") / chars,
        "colon_density": text.count(":") / chars,
        "dash_density": (text.count("-") + text.count("—")) / chars,
    }


def _distance(left: dict[str, float], right: dict[str, float]) -> float:
    return math.sqrt(sum((left[name] - right[name]) ** 2 for name in FEATURES))


def _similarity(distance: float) -> float:
    return 1.0 / (1.0 + distance)


def evaluate_accommodation(req: AccommodationExperimentRequest) -> AccommodationExperimentReport:
    hb = _features(req.human_baseline)
    mb = _features(req.model_baseline)
    hr = _features(req.human_revised)
    mf = _features(req.model_followup)

    initial_distance = _distance(hb, mb)
    final_distance = _distance(hr, mf)
    human_shift = _distance(hb, hr)
    model_shift = _distance(mb, mf)
    cross_convergence = _similarity(final_distance) - _similarity(initial_distance)
    human_retention = _similarity(human_shift)
    model_retention = _similarity(model_shift)

    accommodation = cross_convergence > 0
    if accommodation and human_retention < req.minimum_identity_retention:
        determination = "convergence_with_identity_loss"
    elif accommodation:
        determination = "bounded_accommodation_observed"
    else:
        determination = "no_accommodation_observed"

    return AccommodationExperimentReport(
        experiment_id=req.experiment_id,
        determination=determination,
        metrics=AccommodationMetrics(
            initial_cross_distance=round(initial_distance, 8),
            final_cross_distance=round(final_distance, 8),
            cross_convergence=round(cross_convergence, 8),
            human_shift=round(human_shift, 8),
            model_shift=round(model_shift, 8),
            human_identity_retention=round(human_retention, 8),
            model_style_retention=round(model_retention, 8),
        ),
        governance={
            "accommodation_is_not_origin_attribution": True,
            "agreement_not_required": True,
            "identity_retention_required_for_bounded_accommodation": True,
            "maximum_claim": "observed_feature_convergence",
            "verified_model_origin_claim": False,
        },
    )


@router.post("/accommodation", response_model=AccommodationExperimentReport)
def submit_accommodation_experiment(req: AccommodationExperimentRequest):
    report = evaluate_accommodation(req)
    path = _root() / f"{req.experiment_id}.json"
    if path.exists():
        raise HTTPException(status_code=409, detail="experiment_id already exists")
    path.write_text(json.dumps(report.model_dump(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


@router.get("/{experiment_id}", response_model=AccommodationExperimentReport)
def get_style_experiment(experiment_id: str):
    if not re.fullmatch(r"[A-Za-z0-9._-]+", experiment_id):
        raise HTTPException(status_code=400, detail="invalid experiment_id")
    path = _root() / f"{experiment_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="style experiment not found")
    return AccommodationExperimentReport(**json.loads(path.read_text(encoding="utf-8")))
