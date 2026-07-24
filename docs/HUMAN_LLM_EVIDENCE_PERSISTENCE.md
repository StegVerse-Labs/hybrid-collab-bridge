# Human–LLM Evidence Persistence

Status: ACTIVE

The Human–LLM interoperability runtime now enforces the canonical JSON Schema before structural or BCAT/GCAT admission.

## Runtime sequence

1. Receive or automatically construct the pair assessment.
2. Validate the complete record against `schemas/human_llm_pair_assessment.schema.json`.
3. Run semantic outcome reconstruction and critical-failure precedence.
4. When `mediated_composition` is present, generate one deterministic local-admissibility receipt per declared participant decision.
5. Persist those receipts as `05_mediated_transition_receipts.jsonl` beside the governed session assessment.
6. Bind the receipt-chain reference into the canonical assessment payload.
7. Submit the complete payload through `AdmissionGate` and `CGELightClient`.
8. Persist `04_human_llm_pair_assessment.json` with structural decision, canonical decision, BCAT, GCAT, canonical receipt, and mediated receipt references.
9. Return the same evidence references through the assessment API and automatic `/v1/run` response attachment.

## Evidence contract

The mediated receipt reference contains:

- persisted session path;
- receipt count;
- chain head;
- assessment hash;
- ordered receipt hashes.

Every local receipt contains:

- assessment and trace identifiers;
- transition sequence;
- participant identifier;
- local decision;
- policy and evidence references;
- declared receipt reference;
- claimed composition level;
- assessment hash;
- previous receipt hash;
- deterministic receipt hash.

## Fail-closed rules

- Missing or unavailable schema: deny.
- Schema violation: deny.
- Receipt persistence failure: deny.
- Critical test failure or indeterminate critical test: deny.
- Partial structural result: defer unless canonical admission denies.
- Canonical BCAT/GCAT denial overrides structural allow.
- Publication requires final combined allow.

The receipt chain proves ordering and mutation sensitivity. Signer identity and cryptographic authorization remain a separate release obligation.
