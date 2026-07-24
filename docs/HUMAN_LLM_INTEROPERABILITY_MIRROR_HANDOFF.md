# Human–LLM Interoperability Mirror Handoff

Status: ACTIVE — MEDIATED-COMPOSITION SCHEMA AND ESCALATION ENFORCEMENT BUILT
Repository: StegVerse-Labs/hybrid-collab-bridge
Goal: Convert the Human–LLM Interoperability investigation into a governed, executable evaluation layer for human–model pairs and mediated multi-entity communication.
Last updated: 2026-07-23

## Source-of-truth thesis

Fluent output is not evidence that the human–model pair preserved meaning, understood the result, detected error, or retained evaluative control. The unit under evaluation is the pair and its interaction trace, not the human or model in isolation.

Humans may also form a stateful interoperability layer between otherwise isolated models or entities. Such a pathway must not be elevated from influence to communication, interoperability, governed composition, or collective agency without evidence appropriate to each level.

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

## Runtime proof path

1. Submit a complete assessment with a session path inside the configured `sessions/` root.
2. Validate all nine pair-level tests and review fields.
3. When mediated composition is asserted, identify source, intermediary, and destination participants.
4. Validate continuity, intentionality, channel observations, directional rates, permitted scopes, fidelity dimensions, local admissibility receipts, controls, and null models.
5. Reconstruct the highest evidence-supported level independently of `claimed_level`.
6. Reject any unsupported escalation.
7. Produce `allow`, `defer`, or `deny` admission with critical-failure and local-admissibility precedence.
8. Block governed publication unless the result is a validated `PASS`.
9. Hash the assessment and decision payload.
10. Append a chained CGE-compatible ledger record and receipt.
11. Attach the assessment, admission result, and receipt to the governed session.
12. Retrieve the attached assessment by assessment ID and session path.

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
- `schemas/human_llm_pair_assessment.schema.json`
- `examples/human_llm_pair_assessments.jsonl`
- `tools/validate_human_llm_pair_assessments.py`
- `api/app/governance/human_llm_interoperability.py`
- `tests/test_human_llm_pair_assessments.py`
- `tests/test_human_llm_interoperability_runtime.py`
- `.github/workflows/human-llm-interoperability.yml`

## Current commit tranche

- Schema extension: `479688e5a2ed553eebedbc9e4c050d4eb01029e2`
- Validator enforcement: `789e797c808cff4bc42ba4057e985b891869638b`
- Escalation and agency tests: `7707dc423cb80e2cfc226538ba75f1ba59db14a5`

The files were committed directly. A successful CI or local execution result has not yet been observed in this session, so runtime validation of this tranche remains pending.

## Remaining architecture and integration work

- Add canonical mediated-composition JSONL examples for each supported level and explicit rejected-escalation fixtures.
- Add JSON Schema validation to the deterministic validator or workflow so schema and semantic enforcement run together.
- Add transition-table receipt artifacts for each participant's local admissibility decision.
- Extend the runtime API models and persistence layer to retain the new mediated-composition fields.
- Add live API integration fixtures using FastAPI TestClient.
- Cleanly mount the assessment router at `/v1/interoperability` in `main.py` and remove the startup-order compatibility shim.
- Connect assessment creation automatically to `/v1/run` rather than requiring explicit submission.
- Route assessment decisions through the canonical `AdmissionGate` and `CGELightClient.append_ledger` interfaces after their contracts accept pair-assessment and mediated-composition mutation classes.
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

The mathematical architecture, identified weaknesses, required controls, implementation state, commit identifiers, unverified test status, and next integration sequence are now durably represented. No additional part of this conversation is required to continue the work.
