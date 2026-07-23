# Human–LLM Interoperability Mirror Handoff

Status: ACTIVE
Repository: StegVerse-Labs/hybrid-collab-bridge
Goal: Convert the Human–LLM Interoperability investigation into a governed, executable evaluation layer for human–model pairs.
Last updated: 2026-07-23

## Source-of-truth thesis

Fluent output is not evidence that the human–model pair preserved meaning, understood the result, detected error, or retained evaluative control. The unit under evaluation is the pair and its interaction trace, not the human or model in isolation.

## Current activation goal

Deliver a minimal executable proof path:

1. A pair-level evaluation specification.
2. A machine-readable assessment schema.
3. Example passing and failing assessment records.
4. A deterministic validator.
5. Tests covering meaning preservation, vocabulary collision, boundary control, contradiction detection, evidence classification, audit gap, and review comprehension.
6. Governed receipts suitable for later ingestion into CGE/BCAT/GCAT.

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
- `tests/test_human_llm_pair_assessments.py`

## Remaining integration work

- Connect assessment output to session traces under `sessions/`.
- Add BCAT/GCAT admission rules for assessment completeness and audit-gap thresholds.
- Emit CGE receipt hashes for assessment inputs and decisions.
- Add API endpoint for assessment submission and retrieval.
- Mirror public explanatory material to `StegVerse-Labs/Site` only after checking `docs/SITE_MIRROR_HANDOFF.md` there.
- Evaluate downstream documentation updates for `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki` when release-ready.

## Archival rule

This conversation can be archived when all unique concepts and active obligations are represented by this handoff, committed files, issues, receipts, or other durable records. Repository incompleteness alone is not a reason to retain the conversation.
