# Attribution Trajectory Mirror Handoff

Status: ACTIVE — EXECUTABLE DECISION LAYER BUILT; CONTROLLED EVIDENCE COLLECTION PENDING
Repository: `StegVerse-Labs/hybrid-collab-bridge`
Branch: `main`
Parent handoff: `docs/HUMAN_LLM_INTEROPERABILITY_MIRROR_HANDOFF.md`
Activated: 2026-08-02

## Goal

Test whether equivalent access to a model and source packet reproduces a governing contribution without the originating conceptual trajectory, or whether restoration of that trajectory produces a material and independently measurable reconstruction effect.

## Built in this tranche

- Experimental specification: `docs/ATTRIBUTION_TRAJECTORY_EXPERIMENT.md`
- Machine-readable schema: `schemas/attribution_trajectory_experiment.schema.json`
- Deterministic validator and outcome reconstruction: `tools/validate_attribution_trajectory_experiment.py`
- Tests for both competing hypotheses, conflicting claims, and contamination failure: `tests/test_attribution_trajectory_experiment.py`
- Durable activation/task state: `state/attribution_trajectory_activation.json`

The validator does not trust `claimed_outcome`. It derives one of:

- `supports_interchangeability`
- `supports_trajectory_dependence`
- `indeterminate`

The layer is intentionally capable of producing evidence against either substantive assumption.

## Active execution path

1. Prepare a hash-bound source packet, nominal prompt, output objective, and originating trajectory packet.
2. Assign independent participants to all five required conditions.
3. Collect at least two observations per condition with independent evaluator coverage.
4. Score the six predeclared reconstruction dimensions.
5. Record evaluator agreement and contamination risk.
6. Run `python tools/validate_attribution_trajectory_experiment.py <record.json>`.
7. Preserve the record, derived report, and hashes as governed evidence.
8. Repeat across models/providers and publish bounded findings only after independent replication.

## Internal task coordination

There are no external tasks. The repository-observable task queue is `state/attribution_trajectory_activation.json`. Every obligation has a repository path, status, completion condition, and next executable action. Development must continue by selecting the first task whose dependencies are complete; `blocked` is valid only when the blocking artifact and recovery action are recorded in that file.

## Remaining files and destinations

- Canonical valid experiment fixture → `StegVerse-Labs/hybrid-collab-bridge/examples/attribution_trajectory_experiment.valid.json`
- Explicit contamination/rejected fixture → `StegVerse-Labs/hybrid-collab-bridge/examples/attribution_trajectory_experiment.invalid-contamination.json`
- Evidence packet initializer → `StegVerse-Labs/hybrid-collab-bridge/tools/init_attribution_trajectory_packet.py`
- Evidence packet verifier → `StegVerse-Labs/hybrid-collab-bridge/tools/verify_attribution_trajectory_packet.py`
- CI activation → `StegVerse-Labs/hybrid-collab-bridge/.github/workflows/human-llm-interoperability.yml`
- First controlled evidence bundle → `StegVerse-Labs/hybrid-collab-bridge/evidence/attribution-trajectory/`
- Public presentation after Site handoff review → `StegVerse-Labs/Site`
- Release publication verification → `GCAT-BCAT-Engine/Publisher`
- Admissibility interpretation → `StegVerse-Labs/admissibility-wiki`
- Guardian enforcement interpretation → `StegVerse-Labs/stegguardian-wiki`

## Release boundary

This layer is implemented but not empirically resolved. No universal authorship or trajectory-dependence claim is authorized until controlled records, derived reports, and independent replication are committed.

## Archival rule

This thread may be archived when the implementation, task state, remaining destinations, and next execution action are durably represented here. Repository work continues from this handoff and does not depend on conversational memory.
