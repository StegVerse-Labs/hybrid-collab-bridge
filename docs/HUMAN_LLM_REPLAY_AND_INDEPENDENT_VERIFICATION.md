# Human–LLM Replay and Independent Verification

## Purpose

The replay engine determines whether a persisted Human–LLM interoperability assessment can be reconstructed from its governed session artifacts without trusting the original in-memory admission execution.

The runtime exposes:

- `POST /v1/interoperability/replay/{assessment_id}?session_path=...`
- `GET /v1/interoperability/replay/{assessment_id}?session_path=...`

The POST operation performs a new replay and writes `07_human_llm_replay_verification.json`. The GET operation returns the most recently persisted replay result for that session and assessment.

## Replay inputs

Replay reads only persisted artifacts and configured verification material:

1. `04_human_llm_pair_assessment.json`
2. `05_mediated_transition_receipts.jsonl`, when mediated composition is claimed
3. the configured receipt verification key
4. the canonical assessment schema

It does not accept the original in-memory `AdmissionGate` result as proof.

## Deterministic checks

Replay independently verifies:

- schema conformance;
- assessment hash correspondence;
- recomputed overall outcome;
- recomputed structural decision;
- reconciliation of the structural and stored canonical decisions;
- publication status consistency;
- authenticated mediated receipt signatures;
- receipt sequence and prior-hash continuity;
- receipt assessment hashes;
- persisted chain head and receipt count.

A replay result is `IDENTICAL` only when every required check succeeds. Otherwise it is `MISMATCH` and publication must not treat the replay as reconstructable evidence.

## Result contract

The replay artifact includes:

```json
{
  "assessment_id": "...",
  "replay_status": "IDENTICAL",
  "reconstructable": true,
  "checks": {
    "schema_verified": true,
    "assessment_hash_verified": true,
    "outcome_verified": true,
    "structural_decision_verified": true,
    "canonical_decision_reconciled": true,
    "publication_status_verified": true,
    "receipt_chain_verified": true
  },
  "stored": {},
  "reconstructed": {},
  "receipt_verification": {},
  "errors": []
}
```

## Security and claim boundary

This replay proves deterministic correspondence within the persisted assessment contract. It does not yet prove that an external verifier independently reconstructed the governing BCAT/GCAT policy from immutable canonical policy and delegation snapshots.

Until those snapshots are persisted and verified, the narrow supported claim is:

> The Human–LLM assessment, structural decision, publication status, and authenticated mediated receipt chain can be independently replayed from persisted session evidence.

The broader claim that the complete canonical governance decision is independently reconstructable remains pending immutable policy/delegation snapshot support and asymmetric or managed-key verification.
