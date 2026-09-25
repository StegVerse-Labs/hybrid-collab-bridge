# Human–LLM Interoperability Mirror Handoff

Status: ACTIVE — MEDIATED-COMPOSITION ESCALATION, RECEIPT CHAINING, AND SMALLEST INTEROPERABLE HANDOFF BUILT
Repository: StegVerse-Labs/hybrid-collab-bridge
Goal: Convert the Human–LLM Interoperability investigation into a governed, executable evaluation layer for human–model pairs and mediated multi-entity communication.
Last updated: 2026-07-25

## Source-of-truth thesis

Fluent output is not evidence that the human–model pair preserved meaning, understood the result, detected error, or retained evaluative control. The unit under evaluation is the pair and its interaction trace, not the human or model in isolation.

Humans may also form a stateful interoperability layer between otherwise isolated models or entities. Such a pathway must not be elevated from influence to communication, interoperability, governed composition, or collective agency without evidence appropriate to each level.

## Smallest interoperable handoff implementation

The Conectrr exchange is now represented by `evidence/conectrr/CON-TRACE-001.json`. The external convergence established a deliberately narrow architectural contract: an originating coordination layer may communicate intent, evidence references, reasoning summary, uncertainty, unresolved dependencies, and provenance sufficient for independent downstream reconstruction, while withholding all claims to consent, authority, admissibility, commitment, and execution status.

The implemented contract includes:

- `schemas/smallest_interoperable_handoff.schema.json`
- `examples/smallest_interoperable_handoff.valid.json`
- `examples/smallest_interoperable_handoff.invalid-overreach.json`
- `examples/smallest_interoperable_handoff.invalid-underspecified.json`
- `tools/validate_smallest_interoperable_handoff.py`
- `tests/test_smallest_interoperable_handoff.py`

The deterministic validator rejects both forms of boundary failure:

1. overreach, when the originating layer claims a later consent, authority, admissibility, commitment, or execution decision; and
2. under-specification, when evidence bindings or unresolved downstream dependencies are absent.

No authority is transferred by the trace, contract, fixtures, validator, or external exchange.

## Activation delivered

The repository now contains:

1. Pair-level evaluation specification.
2. Machine-readable pair-assessment schema.
3. Passing and failing assessment records.
4. Deterministic validator.
5. Structural and runtime tests.
6. Session-bound assessment submission and retrieval API.
7. Fail-closed admission decisions with critical-failure precedence.
8. High-consequence review-comprehension enforcement.
9. CGE-compatible hash-chained ledger entries and receipts.
10. Session artifact attachment at `04_human_llm_pair_assessment.json`.
11. GitHub Actions validation workflow.
12. Governed Mediated Transition Composition architecture.
13. Formal separation of influence, relay, semantic mediation, adaptive interoperability, governed composition, and collective agency.
14. Stateful intermediary, developing-medium, directional-rate, permitted-scope, multidimensional-fidelity, continuity, null-model, and falsification fields in the canonical schema.
15. Validator reconstruction of the highest evidence-supported mediated level independently of the claimed level.
16. Fail-closed rejection of unsupported escalation.
17. Participant coverage enforcement across continuity, intentionality, permitted scope, local admissibility, and directional-rate endpoints.
18. Transition-time local admissibility receipt requirements.
19. Explicit prohibition against inferring collective agency from coupling alone.
20. Unit tests for governed composition, relay escalation, broken continuity, local defer, incomplete joint-agency evidence, and rate-limit violations.
21. Deterministic mediated-transition receipt builder.
22. Assessment-bound, participant-sequenced SHA-256 receipt chains with genesis and prior-hash linkage.
23. Receipt-chain tests covering participant order, payload hashing, mutation sensitivity, and pair-only traces.
24. CI path coverage and execution steps for receipt generation and receipt tests.
25. Smallest interoperable handoff trace, schema, deterministic validator, valid fixture, and bidirectional rejection fixtures.

## Runtime proof path

1. Submit a complete assessment with a session path inside the configured `sessions/` root.
2. Validate all nine pair-level tests and review fields.
3. When mediated composition is asserted, identify source, intermediary, and destination participants.
4. Validate continuity, intentionality, channel observations, directional rates, permitted scopes, fidelity dimensions, local admissibility receipts, controls, and null models.
5. Reconstruct the highest evidence-supported level independently of `claimed_level`.
6. Reject any unsupported escalation.
7. Produce `allow`, `defer`, or `deny` admission with critical-failure and local-admissibility precedence.
8. Block governed publication unless the result is a validated `PASS`.
9. Canonicalize and hash the complete assessment.
10. Generate one local-admissibility receipt per participant in declared transition order.
11. Bind each receipt to the assessment hash, prior receipt hash, participant, decision, policy, evidence, claimed level, trace, and declared receipt reference.
12. Append the resulting chain head to the governed ledger path.
13. Attach the assessment, admission result, and receipts to the governed session.
14. Retrieve the attached assessment and receipts by assessment ID and session path.
15. Validate every smallest interoperable handoff before downstream evaluation.

Current transitional API path:

- `POST /v1/dashboard/v1/interoperability/assessments`
- `GET /v1/dashboard/v1/interoperability/assessments/{assessment_id}`

The duplicated namespace is temporary because `main.py` currently registers only the dashboard governance router. A later router cleanup should mount the assessment router directly at `/v1/interoperability`.

## Required distinctions

- Expression capability is not interpretive capability.
- Interpretive capability is not evaluative capability.
- Human presence is not human control.
- Review is not comprehension.
- Rhetorical interoperability is not structural interoperability.
- Approval is not continuity.
- Execution is not admissibility.
- Causal influence is not information transfer.
- Information transfer is not communication.
- Communication is not interoperability.
- Interoperability is not governed composition.
- Coupling is not joint agency, shared cognition, or collective identity.
- Discovery is not consent.
- Recommendation is not authority.
- Handoff sufficiency is not admissibility.

## Mediated-composition architecture

The architecture is formally represented as constrained composition among independently instantiated transition systems:

```text
G = T_A tensor_(M, Pi, R, Omega) T_H tensor_(M, Pi, R, Omega) T_B
```

Where:

- `M` is a shared or developing perception and expression medium;
- `Pi` is transition-time admissibility;
- `R` is directional rate;
- `Omega` is permitted scope or extent;
- `T_H` is a stateful intermediary, not a passive relay.

The medium may evolve through repeated interaction. Meaning preservation is evaluated across symbolic, semantic, pragmatic, causal, and governance fidelity rather than by mutual information or textual similarity alone.

Communication does not require intent, but intentionality is recorded without invention. Claims of learning the intermediary distinguish population-level language regularities, individual intermediary patterns, and situational patterns. Null explanations and falsification controls are mandatory for claims of adaptive interoperability.

## Evidence escalation rules now enforced

- `influence`: default when a governed channel has not been established.
- `relay`: requires at least three declared participants with source, intermediary, and destination roles plus channel observations.
- `semantic_mediation`: additionally requires semantic, pragmatic, and causal fidelity of at least `0.70` with evidence.
- `adaptive_interoperability`: additionally requires adaptation evidence, paraphrase and intermediary-substitution controls, and at least one tested null model.
- `governed_composition`: additionally requires verified continuity for every participant, local `allow` decisions with policy/evidence/receipt references, and governance fidelity of at least `0.70`.
- `collective_agency`: additionally requires affirmative evidence for persistent joint state, integrated objective selection, shared memory or continuity, a joint decision boundary, joint error correction, and accountable joint action.

## Receipt-chain contract

The receipt builder at `tools/build_mediated_transition_receipts.py`:

- ignores pair-only records without mediated composition;
- canonicalizes JSON with sorted keys and compact separators;
- computes a SHA-256 assessment hash;
- starts each output chain from a fixed 64-zero genesis hash;
- emits one receipt for each local admissibility decision;
- links each receipt through `previous_hash`;
- computes `receipt_hash` over the complete receipt payload excluding only `receipt_hash` itself;
- carries the chain head across multiple assessment records in the same input file;
- fails on malformed JSON or non-object records.

This chain proves record ordering and detects mutation. It does not by itself prove signer identity or cryptographic authorization; signatures and canonical ecosystem ledger integration remain separate obligations.

## Error attribution classes

- human_originated
- model_originated
- interaction_originated
- review_failed
- translation_originated
- boundary_originated
- amplification_originated
- continuity_originated
- mediation_originated
- provenance_originated
- agency_inflation

## Active files

- `docs/HUMAN_LLM_INTEROPERABILITY_SPEC.md`
- `docs/GOVERNED_MEDIATED_TRANSITION_COMPOSITION.md`
- `docs/HUMAN_LLM_INTEROPERABILITY_MIRROR_HANDOFF.md`
- `schemas/human_llm_pair_assessment.schema.json`
- `schemas/smallest_interoperable_handoff.schema.json`
- `evidence/conectrr/CON-TRACE-001.json`
- `examples/human_llm_pair_assessments.jsonl`
- `examples/smallest_interoperable_handoff.valid.json`
- `examples/smallest_interoperable_handoff.invalid-overreach.json`
- `examples/smallest_interoperable_handoff.invalid-underspecified.json`
- `tools/validate_human_llm_pair_assessments.py`
- `tools/validate_smallest_interoperable_handoff.py`
- `tools/build_mediated_transition_receipts.py`
- `api/app/governance/human_llm_interoperability.py`
- `tests/test_human_llm_pair_assessments.py`
- `tests/test_human_llm_interoperability_runtime.py`
- `tests/test_mediated_transition_receipts.py`
- `tests/test_smallest_interoperable_handoff.py`
- `.github/workflows/human-llm-interoperability.yml`

## Current implementation tranche

- Conectrr trace: `0388dc287d2df7a2ec62a3c28e9cf9fd5c160668`
- Handoff schema: `3e460da59613ab1dec29686c036305ef3462684a`
- Valid fixture: `d276652ac2069ec8924d60b693f18c1853733d5b`
- Overreach fixture: `041746822010ca756f2ec03e306c6c75b154f7ac`
- Under-specification fixture: `2e91d73cb5fa86d702a46b5709fc2b5dfadd6a93`
- Deterministic validator: `9d4b650d3480674566ed0166b2d3a36451d8f9b4`
- Contract tests: `6251c296de213793c41d0d9c00518a08f2e91025`

Files were committed directly. Repository-hosted CI observation remains separate from implementation completion.

## Remaining architecture and integration work

- Add canonical mediated-composition JSONL examples for each supported level and explicit rejected-escalation fixtures.
- Add JSON Schema validation to the deterministic validator or workflow so schema and semantic enforcement run together.
- Persist generated transition receipts beside governed session artifacts and return receipt references through the API.
- Extend the runtime API models and persistence layer to retain the new mediated-composition fields.
- Add live API integration fixtures using FastAPI TestClient.
- Cleanly mount the assessment router at `/v1/interoperability` in `main.py` and remove the startup-order compatibility shim.
- Connect assessment creation automatically to `/v1/run` rather than requiring explicit submission.
- Route assessment decisions and generated receipt chain heads through the canonical `AdmissionGate` and `CGELightClient.append_ledger` interfaces after their contracts accept pair-assessment and mediated-composition mutation classes.
- Add signer identity, signature, and key-reference fields when the canonical receipt contract is available.
- Check `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` before public mirroring.
- At release readiness, verify downstream updates for `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Known installation destinations

- Source architecture and runtime: `StegVerse-Labs/hybrid-collab-bridge`.
- Public governed presentation after Site handoff review: `StegVerse-Labs/Site`.
- Publication pipeline verification at release readiness: `GCAT-BCAT-Engine/Publisher`.
- Admissibility vocabulary and examples at release readiness: `StegVerse-Labs/admissibility-wiki`.
- Guardian enforcement interpretation at release readiness: `StegVerse-Labs/stegguardian-wiki`.

## Archival rule

This conversation can be archived when all unique concepts and active obligations are represented by this handoff, committed files, issues, receipts, or other durable records. Repository incompleteness alone is not a reason to retain the conversation.

The Conectrr convergence record, smallest interoperable handoff contract, bidirectional failure fixtures, validator, tests, prior mediated-composition architecture, implementation commit identifiers, remaining integrations, and authority boundaries are durably represented. No additional part of this conversation is required to continue the work.


## 2026-09-25 common-goal mutual-adaptation reconciliation

Existing-owner candidate, not a new authority or admitted Registry task: see [`COMMON_GOAL_MUTUAL_ADAPTATION_RECONCILIATION.md`](COMMON_GOAL_MUTUAL_ADAPTATION_RECONCILIATION.md). Reuses the current mediated-composition evaluator and local admissibility controls; defines seven frozen acceptance tests for compatible goals, changing capacities, independently observed adaptation, revocation, viability, provenance, and authentic custody. Central Task Registry generation 243 has no exact task identity for this extension; authorized coordination must select existing canonical ownership and allocate/bind COSV before any canonical status claim. No production execution, live organism intervention, runtime disposition, or Master Records reconstruction is claimed by this source candidate.

### 2026-09-25 implementation candidate (draft PR #31)

The optional `common_goal_adaptation` assessment is validated by the existing `tools/validate_human_llm_pair_assessments.py` and corresponding JSON Schema. Seven source-level predicates are implemented in `tools/evaluate_common_goal_adaptation.py` with positive, conflicting-goal, capacity-change, held-out/null-control, revocation, participant-viability, provenance, and local-replay tests in `tests/test_common_goal_adaptation.py`; existing CI includes that test file. The evaluator can return PASS/FAIL/INDETERMINATE as source-only classifications and checks declared expectations against independently recomputed results. Synthetic receipt references never establish authoritative local admissibility or Master Records custody. No live-system/organism claim is made. Central admission request: `StegVerse-Labs/.github#2726`; existing bridge owner: `#6`. Registry/COSV and actual governed execution remain subject to existing authorized coordination.

### 2026-09-25 post-revocation source repair (PR #31)

The optional synthetic evaluator independently recomputes the eligible goal intersection after any participant revokes permission. The assessment now explicitly records `selected_goal_after_revocation`; this cannot rely on `goal_recomputed_after_revocation` alone. A remaining shared goal requires at least two independently sourced, currently consenting, non-revoked participants; otherwise the selected post-revocation goal must be null. Three adversarial regression tests cover stale goals after withdrawal, remaining eligible participants, and missing post-revocation selection. This is source-level validation only, not authenticated consent, SDK/InTr admission, or Master Records custody. Central admission #2726 remains separate.
