# Human–LLM Interoperability Mirror Handoff

Status: ACTIVE — RUNTIME INTEGRATION BUILT; MEDIATED-COMPOSITION ARCHITECTURE DOCUMENTED
Repository: StegVerse-Labs/hybrid-collab-bridge
Goal: Convert the Human–LLM Interoperability investigation into a governed, executable evaluation layer for human–model pairs and mediated multi-entity communication.
Last updated: 2026-07-23

## Source-of-truth thesis

Fluent output is not evidence that the human–model pair preserved meaning, understood the result, detected error, or retained evaluative control. The unit under evaluation is the pair and its interaction trace, not the human or model in isolation.

Humans may also form a stateful interoperability layer between otherwise isolated models or entities. Such a pathway must not be elevated from influence to communication, interoperability, governed composition, or collective agency without evidence appropriate to each level.

## Activation delivered

The repository now contains:

1. Pair-level evaluation specification.
2. Machine-readable assessment schema.
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
13. Formal separation of relay, semantic mediation, adaptive interoperability, and governed composition.
14. Stateful intermediary, developing-medium, directional-rate, permitted-scope, multidimensional-fidelity, continuity, null-model, and falsification requirements.
15. Explicit prohibition against inferring collective agency from coupling alone.

## Runtime proof path

1. Submit a complete assessment with a session path inside the configured `sessions/` root.
2. Validate all nine required tests and review fields.
3. Reconstruct the required overall outcome.
4. Produce `allow`, `defer`, or `deny` admission.
5. Block governed publication unless the result is a validated `PASS`.
6. Hash the assessment and decision payload.
7. Append a chained CGE-compatible ledger record and receipt.
8. Attach the assessment, admission result, and receipt to the governed session.
9. Retrieve the attached assessment by assessment ID and session path.

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

The medium may evolve through repeated interaction. Meaning preservation must be evaluated across symbolic, semantic, pragmatic, causal, and governance fidelity rather than by mutual information or textual similarity alone.

Communication does not require intent, but intentionality must be recorded without invention. Claims of learning the intermediary must distinguish population-level language regularities, individual intermediary patterns, and situational patterns. Null explanations and falsification controls are mandatory for claims of adaptive interoperability.

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

## Remaining architecture and integration work

- Extend `schemas/human_llm_pair_assessment.schema.json` with mediated participants, continuity, channel, intentionality, directional rate, permitted scope, fidelity, local admissibility, and null-model fields.
- Extend the deterministic validator to reject unsupported escalation from relay to semantic mediation, adaptive interoperability, governed composition, or collective agency.
- Add controlled examples and tests for intermediary substitution, paraphrase, delay, adversarial relay, hidden provenance, common-training controls, and independent convergence.
- Add transition-table receipts for each participant's local admissibility decision.
- Cleanly mount the assessment router at `/v1/interoperability` in `main.py` and remove the startup-order compatibility shim.
- Connect assessment creation automatically to `/v1/run` rather than requiring explicit submission.
- Route assessment decisions through the canonical `AdmissionGate` and `CGELightClient.append_ledger` interfaces after their contracts accept pair-assessment and mediated-composition mutation classes.
- Add live API integration fixtures using FastAPI TestClient.
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

The mathematical architecture, identified weaknesses, required controls, and implementation sequence from the current discussion are now durably represented by this handoff and the committed architecture documents. No additional part of this conversation is required to continue the work.
