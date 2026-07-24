# Human–LLM Mediated Receipt Authentication

Status: ACTIVE — INITIAL AUTHENTICATED RECEIPT CONTRACT

## Purpose

The mediated-transition chain previously proved deterministic ordering and mutation sensitivity, but a hash alone did not establish which governed entity authorized the receipt. The runtime now authenticates every mediated local-admissibility receipt before persistence.

## Current signer contract

The initial deployable implementation uses HMAC-SHA256.

Required runtime configuration:

- `HCB_RECEIPT_SIGNING_KEY`: secret signing material; never persisted in receipts or session artifacts.
- `HCB_RECEIPT_SIGNER_ID`: governed signer identity. Default: `human-llm-pair-assessor`.
- `HCB_RECEIPT_SIGNING_KEY_REF`: non-secret key reference. Default: `env:HCB_RECEIPT_SIGNING_KEY`.

A mediated assessment fails closed when signing material is unavailable. Pair-only assessments do not require mediated-transition signatures because no participant transition chain is emitted.

## Receipt fields

Each authenticated receipt includes:

- receipt type;
- assessment and trace identifiers;
- transition sequence;
- participant identifier;
- local admissibility decision;
- policy and evidence references;
- declared upstream receipt reference;
- claimed mediated level;
- assessment hash;
- previous receipt hash;
- receipt hash;
- signer identity;
- key reference;
- signature algorithm;
- signature.

## Verification order

Verification reconstructs and checks independently:

1. The unsigned transition payload hash.
2. The signer identity.
3. The key reference.
4. The declared signature algorithm.
5. The HMAC signature using resolved signing material.
6. The sequence number.
7. The previous-hash linkage.
8. The final chain head.

Generated receipts are verified before being written. Verification failure prevents persistence and forces the assessment admission path to `deny` with an `INDETERMINATE` outcome.

## Session artifacts

Mediated assessments now produce:

- `04_human_llm_pair_assessment.json`
- `05_mediated_transition_receipts.jsonl`
- `06_mediated_transition_verification.json`

The assessment artifact and API result reference the receipt file, verification file, signer identity, key reference, signature algorithm, chain head, receipt hashes, and aggregate verification status.

## Key rotation

Rotation changes `HCB_RECEIPT_SIGNING_KEY_REF` with the signing material. Existing receipts retain their original key reference and must be verified using the corresponding historical key. A key registry or KMS resolver should retain verification capability without retaining unnecessary signing authority.

Never reuse a key reference for different secret material. Never expose the signing secret through receipts, logs, API responses, or repository configuration.

## Security boundary

HMAC provides authenticity only to verifiers that possess the shared secret. It does not provide public, non-repudiable signatures. This implementation is therefore an internal governed-authentication boundary and a stable interface for later replacement by Ed25519, hardware-backed signing, or a KMS/HSM signer.

Hash continuity is not signer identity. Signer identity is not authority. Authority remains subject to policy, delegation, local admissibility, continuity, and canonical BCAT/GCAT admission.
