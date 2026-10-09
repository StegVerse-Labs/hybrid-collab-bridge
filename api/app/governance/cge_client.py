"""CGE Light client for per-org governance.

Embedded mode is the only mode. The former ``remote`` mode (HTTP POSTs to
``{HCB_CGE_ENDPOINT}/v1/ingest`` and ``/v1/ledger/append``) was an external
service dependency and a competing ledger; HCB holds no ledger authority. Any
non-embedded mode fails closed with a six-field disposition and contacts
nothing.
"""
from __future__ import annotations
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from .entity import EntityIdentity

EMBEDDED_MODE = "embedded"
OWNING_EXISTING_GOAL = "HCB-VERSIONED-CONTRACT-038"


def remote_cge_removed(mode: str) -> Dict[str, Any]:
    """Six-field FAIL_CLOSED disposition for a requested non-embedded CGE mode."""
    return {
        "state": "BLOCKED",
        "disposition": "FAIL_CLOSED",
        "error": "REMOTE_CGE_REMOVED",
        "requested_cge_mode": mode,
        "failure_code": "REMOTE_CGE_REMOVED",
        "failed_predicate": f"HCB_CGE_MODE == 'embedded' (got {mode!r})",
        "required_evidence_or_repair": (
            "unset HCB_CGE_MODE or set it to 'embedded'; the remote CGE service and "
            "HCB_CGE_ENDPOINT were removed and HCB holds no ledger authority"
        ),
        "retry_entrypoint": "restart with HCB_CGE_MODE=embedded",
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": "immediately after reconfiguring; nothing waits for a remote CGE",
        "admissible": False,
        "remote_contacted": False,
        "authority_effect": False,
    }


class RemoteCGERemoved(RuntimeError):
    """Raised when a ledger append is requested in a removed (non-embedded) mode."""

    def __init__(self, mode: str):
        self.disposition = remote_cge_removed(mode)
        super().__init__(self.disposition["failed_predicate"])


class CGELightClient:
    def __init__(
        self,
        org_id: str,
        mode: str = EMBEDDED_MODE,
        cge_path: Optional[str] = None,
    ):
        self.org_id = org_id
        self.mode = mode
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

        if self.mode != EMBEDDED_MODE:
            return remote_cge_removed(self.mode)
        return self._ingest_embedded(ingest_obj)

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
        if self.mode != EMBEDDED_MODE:
            raise RemoteCGERemoved(self.mode)
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
