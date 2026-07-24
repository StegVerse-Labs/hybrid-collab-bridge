"""CGE Light client for per-org governance."""
from __future__ import annotations
import os
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

from .entity import EntityIdentity


class CGELightClient:
    def __init__(
        self,
        org_id: str,
        mode: str = "embedded",
        endpoint: Optional[str] = None,
        cge_path: Optional[str] = None,
    ):
        self.org_id = org_id
        self.mode = mode
        self.endpoint = endpoint
        self.cge_path = Path(cge_path) if cge_path else Path(__file__).resolve().parents[3] / "cge_light"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for subdir in ["state", "meta/receipts", "meta/status", "sandbox"]:
            (self.cge_path / subdir).mkdir(parents=True, exist_ok=True)

    async def ingest(
        self,
        payload: Dict[str, Any],
        source: str,
        actor: EntityIdentity,
        mutation_class: str = "ingest",
    ) -> Dict[str, Any]:
        ingest_obj = {
            "type": mutation_class,
            "source": source,
            "actor": actor.to_dict(),
            "payload": payload,
            "timestamp": int(time.time()),
            "ingest_id": str(uuid.uuid4()),
        }

        if self.mode == "embedded":
            return self._ingest_embedded(ingest_obj)
        elif self.mode == "remote":
            return await self._ingest_remote(ingest_obj)
        else:
            try:
                return self._ingest_embedded(ingest_obj)
            except Exception:
                if self.endpoint:
                    return await self._ingest_remote(ingest_obj)
                raise

    def _ingest_embedded(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        import sys
        cge_path = str(self.cge_path)
        if cge_path not in sys.path:
            sys.path.insert(0, cge_path)
        from cge.ingest import ingest_object
        from cge.policy import evaluate_bcat, evaluate_gcat

        result = ingest_object(obj, source=obj["source"])
        # Preserve the exact post-ingest object supplied to policy evaluation. This
        # includes commit-time identifiers and timestamps and is therefore the only
        # sufficient deterministic input for later BCAT/GCAT regeneration.
        evaluation_input = json.loads(json.dumps(result))
        bcat = evaluate_bcat(evaluation_input)
        gcat = evaluate_gcat(bcat)

        result["bcat"] = bcat
        result["gcat"] = gcat
        result["admissible"] = self._check_admissibility(bcat, gcat)
        result["evaluation_input"] = evaluation_input
        result["evaluator"] = {
            "mode": "embedded",
            "bcat_callable": "cge.policy.evaluate_bcat",
            "gcat_callable": "cge.policy.evaluate_gcat",
        }
        return result

    async def _ingest_remote(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self.endpoint}/v1/ingest",
                json=obj,
                headers={"X-ORG-ID": self.org_id},
            )
            r.raise_for_status()
            result = r.json()
            if isinstance(result, dict):
                result.setdefault("evaluator", {
                    "mode": "remote",
                    "endpoint": self.endpoint,
                    "regeneration_supported": bool(result.get("evaluation_input")),
                })
            return result

    def _check_admissibility(self, bcat: Dict, gcat: Dict) -> bool:
        constitution_path = self.cge_path / "repo_constitution.txt"
        if not constitution_path.exists():
            return True

        import yaml
        constitution = yaml.safe_load(constitution_path.read_text())
        profile = constitution.get("threshold_profiles", {}).get("standard", {})

        checks = [
            bcat.get("observability", 0) >= profile.get("observability_min", 0.6),
            bcat.get("context_stability", 0) >= profile.get("context_stability_min", 0.5),
            bcat.get("authority_clarity", 0) >= profile.get("authority_clarity_min", 0.5),
            bcat.get("reversibility_margin", 0) >= profile.get("reversibility_margin_min", 0.3),
            bcat.get("risk", 1.0) <= profile.get("risk_max", 0.7),
        ]
        return all(checks)

    async def append_ledger(
        self,
        mutation_class: str,
        actor: EntityIdentity,
        payload: Dict[str, Any],
        bcat: Dict[str, Any],
        gcat: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self.mode == "embedded":
            import sys
            cge_path = str(self.cge_path)
            if cge_path not in sys.path:
                sys.path.insert(0, cge_path)
            from cge.ledger import append_ledger_entry
            from cge.receipts import verify_receipt

            receipt = append_ledger_entry(
                mutation_class=mutation_class,
                actor=actor.entity_id,
                payload=payload,
                bcat=bcat,
                gcat=gcat,
            )
            verified = verify_receipt(receipt)
            receipt["verified"] = verified
            return receipt
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self.endpoint}/v1/ledger/append",
                    json={
                        "mutation_class": mutation_class,
                        "actor": actor.to_dict(),
                        "payload": payload,
                        "bcat": bcat,
                        "gcat": gcat,
                    },
                    headers={"X-ORG-ID": self.org_id},
                )
                r.raise_for_status()
                return r.json()

    async def chain_receipt(
        self,
        previous_receipt_id: Optional[str],
        current_receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        chain_entry = {
            "chain_id": str(uuid.uuid4()),
            "previous_receipt_id": previous_receipt_id,
            "current_receipt_id": current_receipt.get("receipt_id"),
            "timestamp": int(time.time()),
            "org_id": self.org_id,
        }
        chain_path = self.cge_path / "meta" / "receipt_chains.jsonl"
        with chain_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(chain_entry, sort_keys=True) + "\n")
        return chain_entry
