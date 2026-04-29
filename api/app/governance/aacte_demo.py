"""AaCT-E Demo Repo — GCAT/BCAT Experiment Pipeline.

Instantiates the full GCAT/BCAT formalism for:
- Admissibility computation
- Capability assessment
- Authority tracking
- Trust continuity verification

Repo: github.com/AaCT-E/demo
"""
from __future__ import annotations
import json
from typing import Dict, Any, List
from dataclasses import dataclass

from .entity import EntityIdentity
from .cge_client import CGELightClient


@dataclass
class GCATResult:
    """GCAT capability assessment result."""
    g: float  # Governed
    c: float  # Capable
    a: float  # Accountable
    t: float  # Trusted
    normalized: bool
    threshold_met: bool


@dataclass
class BCATResult:
    """BCAT baseline capability assessment."""
    observability: float
    context_stability: float
    trust_continuity: float
    authority_clarity: float
    reversibility_margin: float
    risk: float
    threshold_met: bool


class AaCTEDemoPipeline:
    """AaCT-E demo pipeline for GCAT/BCAT experiments.

    Usage:
        pipeline = AaCTEDemoPipeline(cge_client, constitution)

        # Run experiment
        result = await pipeline.run_experiment(
            experiment_id="exp-001",
            hypothesis="BCAT threshold 0.6 is sufficient for safe deployment",
            parameters={"threshold": 0.6, "samples": 100},
            entity=experiment_entity,
        )

        # Result includes full GCAT/BCAT assessment + receipt
    """

    def __init__(self, cge_client: CGELightClient, constitution: Dict[str, Any]):
        self.cge = cge_client
        self.constitution = constitution
        self.thresholds = constitution.get("threshold_profiles", {}).get("standard", {})

    async def run_experiment(
        self,
        experiment_id: str,
        hypothesis: str,
        parameters: Dict[str, Any],
        entity: EntityIdentity,
    ) -> Dict[str, Any]:
        """Run a GCAT/BCAT experiment with full governance."""

        # 1. Ingest experiment proposal
        proposal = {
            "type": "experiment_proposal",
            "experiment_id": experiment_id,
            "hypothesis": hypothesis,
            "parameters": parameters,
        }

        ingest_result = await self.cge.ingest(
            payload=proposal,
            source="aacte/demo",
            actor=entity,
            mutation_class="create",
        )

        bcat = ingest_result.get("bcat", {})
        gcat_raw = ingest_result.get("gcat", {})

        # 2. Evaluate BCAT
        bcat_result = BCATResult(
            observability=bcat.get("observability", 0),
            context_stability=bcat.get("context_stability", 0),
            trust_continuity=bcat.get("trust_continuity", 0),
            authority_clarity=bcat.get("authority_clarity", 0),
            reversibility_margin=bcat.get("reversibility_margin", 0),
            risk=bcat.get("risk", 1.0),
            threshold_met=self._check_bcat_thresholds(bcat),
        )

        # 3. Evaluate GCAT
        gcat_result = GCATResult(
            g=gcat_raw.get("g", 0.25),
            c=gcat_raw.get("c", 0.25),
            a=gcat_raw.get("a", 0.25),
            t=gcat_raw.get("t", 0.25),
            normalized=True,
            threshold_met=bcat_result.threshold_met,
        )

        # 4. Append to ledger
        receipt = await self.cge.append_ledger(
            mutation_class="create",
            actor=entity,
            payload=proposal,
            bcat=bcat,
            gcat=gcat_raw,
        )

        return {
            "experiment_id": experiment_id,
            "status": "admitted" if bcat_result.threshold_met else "deferred",
            "bcat": {
                "observability": bcat_result.observability,
                "context_stability": bcat_result.context_stability,
                "trust_continuity": bcat_result.trust_continuity,
                "authority_clarity": bcat_result.authority_clarity,
                "reversibility_margin": bcat_result.reversibility_margin,
                "risk": bcat_result.risk,
                "threshold_met": bcat_result.threshold_met,
            },
            "gcat": {
                "g": gcat_result.g,
                "c": gcat_result.c,
                "a": gcat_result.a,
                "t": gcat_result.t,
                "threshold_met": gcat_result.threshold_met,
            },
            "receipt": receipt,
            "hypothesis": hypothesis,
            "parameters": parameters,
        }

    def _check_bcat_thresholds(self, bcat: Dict[str, float]) -> bool:
        """Check if BCAT scores meet standard thresholds."""
        checks = [
            bcat.get("observability", 0) >= self.thresholds.get("observability_min", 0.6),
            bcat.get("context_stability", 0) >= self.thresholds.get("context_stability_min", 0.5),
            bcat.get("authority_clarity", 0) >= self.thresholds.get("authority_clarity_min", 0.5),
            bcat.get("reversibility_margin", 0) >= self.thresholds.get("reversibility_margin_min", 0.3),
            bcat.get("risk", 1.0) <= self.thresholds.get("risk_max", 0.7),
        ]
        return all(checks)

    async def validate_experiment_result(
        self,
        experiment_id: str,
        result_data: Dict[str, Any],
        entity: EntityIdentity,
    ) -> Dict[str, Any]:
        """Validate experiment results against GCAT/BCAT."""

        proposal = {
            "type": "experiment_validation",
            "experiment_id": experiment_id,
            "result_data": result_data,
        }

        ingest_result = await self.cge.ingest(
            payload=proposal,
            source="aacte/demo/validation",
            actor=entity,
            mutation_class="derive",
        )

        bcat = ingest_result.get("bcat", {})
        gcat = ingest_result.get("gcat", {})

        receipt = await self.cge.append_ledger(
            mutation_class="derive",
            actor=entity,
            payload=proposal,
            bcat=bcat,
            gcat=gcat,
        )

        return {
            "experiment_id": experiment_id,
            "validation_status": "passed" if self._check_bcat_thresholds(bcat) else "failed",
            "bcat": bcat,
            "gcat": gcat,
            "receipt": receipt,
        }
