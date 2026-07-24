# Human–LLM Interoperability Mirror Handoff

Status: ACTIVE — RUNTIME INTEGRATION BUILT
Repository: StegVerse-Labs/hybrid-collab-bridge
Goal: Convert the Human–LLM Interoperability investigation into a governed, executable evaluation layer for human–model pairs.
Last updated: 2026-07-23

## Source-of-truth thesis

Fluent output is not evidence that the human–model pair preserved meaning, understood the result, detected error, or retained evaluative control. The unit under evaluation is the pair and its interaction trace, not the human or model in isolation.

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

## Error attribution classes

- human_originated
- model_originated
- interaction_originated
- review_failed
- translation_originated
- boundary_originated
- amplification_originated

## Active files

- `docs/HUMAN_LLM_INTEROPERABILITY_SPEC.md`
- `schemas/human_llm_pair_assessment.schema.json`
- `examples/human_llm_pair_assessments.jsonl`
- `tools/validate_human_llm_pair_assessments.py`
- `api/app/governance/human_llm_interoperability.py`
- `tests/test_human_llm_pair_assessments.py`
- `tests/test_human_llm_interoperability_runtime.py`
- `.github/workflows/human-llm-interoperability.yml`

## Remaining integration work

- Cleanly mount the assessment router at `/v1/interoperability` in `main.py` and remove the startup-order compatibility shim.
- Connect assessment creation automatically to `/v1/run` rather than requiring explicit submission.
- Route assessment decisions through the canonical `AdmissionGate` and `CGELightClient.append_ledger` interfaces after their contracts accept pair-assessment mutation classes.
- Add live API integration fixtures using FastAPI TestClient.
- Check `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` before public mirroring.
- At release readiness, verify downstream updates for `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Archival rule

This conversation can be archived when all unique concepts and active obligations are represented by this handoff, committed files, issues, receipts, or other durable records. Repository incompleteness alone is not a reason to retain the conversation.
