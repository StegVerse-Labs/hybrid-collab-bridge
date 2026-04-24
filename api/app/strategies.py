"""Consensus strategy with admission gates.

Every proposal is ingested, evaluated, and receipted individually.
The referee merge is a separate derive mutation with its own receipt.
"""
from typing import List, Dict, Any
from .tasks import Task
from .registry import ProviderRegistry
from .governance.entity import EntityIdentity
from .governance.admission import AdmissionGate, AdmissionResult


async def governed_consensus(
    reg: ProviderRegistry,
    gate: AdmissionGate,
    experts: List[str],
    prompt: str,
    opts: Dict[str, Any],
    bridge_entity: EntityIdentity,
) -> Dict[str, Any]:
    """Run consensus with full admission at every step."""
    proposals = []
    previous_receipt_id = None

    # Phase 1: Ingest the collaboration request itself
    request_admission = await gate.admit_proposal(
        proposal={
            "type": "collaboration_request",
            "prompt": prompt,
            "experts": experts,
            "strategy": "consensus",
            "options": opts,
        },
        actor=bridge_entity,
        source="hybrid-collab-bridge/request",
    )

    if request_admission.decision == "deny":
        return {
            "proposals": [],
            "final": request_admission,
            "chain_id": None,
            "status": "DENIED",
        }

    previous_receipt_id = request_admission.receipt.get("receipt_id")

    # Phase 2: Run each expert, admit each output
    for name in experts:
        prov = reg.get(name)
        if not prov or not prov.supports("text-generate"):
            continue

        expert_entity = EntityIdentity(
            entity_id=f"{bridge_entity.entity_id}-{name}",
            entity_type="llm_adapter",
            org_id=bridge_entity.org_id,
            owner_human=bridge_entity.owner_human,
            capability_set=["text-generate"],
            governance_scope="internal",
        )

        out = await prov.run(Task("text-generate", prompt, opts))

        admission = await gate.admit_proposal(
            proposal={
                "type": "expert_output",
                "expert": name,
                "output": out.get("text", ""),
                "prompt_hash": hash(prompt) & 0xFFFFFFFF,
            },
            actor=expert_entity,
            source=f"hybrid-collab-bridge/expert/{name}",
        )

        proposals.append({
            "who": name,
            "out": out,
            "admission": admission,
        })

        if previous_receipt_id:
            await gate.cge.chain_receipt(previous_receipt_id, admission.receipt)
        previous_receipt_id = admission.receipt.get("receipt_id")

    # Phase 3: Referee merge (derive mutation)
    if proposals:
        referee_entity = EntityIdentity(
            entity_id=f"{bridge_entity.entity_id}-referee",
            entity_type="consensus_engine",
            org_id=bridge_entity.org_id,
            owner_human=bridge_entity.owner_human,
            capability_set=["consensus", "merge"],
            governance_scope="internal",
        )

        admitted_proposals = [
            p for p in proposals if p["admission"].decision == "allow"
        ]

        if not admitted_proposals:
            return {
                "proposals": proposals,
                "final": proposals[0]["admission"],
                "chain_id": previous_receipt_id,
                "status": "DEFERRED",
            }

        merged_prompt = "Synthesize a concise final answer from these ADMITTED proposals:\n\n"
        for p in admitted_proposals:
            merged_prompt += f"- {p['who']}: {p['out'].get('text','')}\n"

        referee = reg.get(experts[0])
        merged = await referee.run(Task("text-generate", merged_prompt, {"temperature": 0.2}))

        merge_admission = await gate.admit_consensus_merge(
            proposals=admitted_proposals,
            merge_output=merged,
            referee_actor=referee_entity,
        )

        if previous_receipt_id:
            await gate.cge.chain_receipt(previous_receipt_id, merge_admission.receipt)

        return {
            "proposals": proposals,
            "final": merge_admission,
            "chain_id": merge_admission.receipt.get("receipt_id"),
            "status": "OK" if merge_admission.decision == "allow" else "DEFERRED",
        }

    return {
        "proposals": [],
        "final": request_admission,
        "chain_id": previous_receipt_id,
        "status": "DENIED",
    }
