# Hybrid Collab Bridge Mirror Handoff

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Source of truth

This file is the current handoff and task source of truth for this repository.

## Current goal

```text
Goal: govern internal LLM proposals through deterministic normalization and artifact integrity before the next ecosystem boundary
Phase: internal-adapter-integrity-contract-installed
Result: NORMALIZATION_GREEN_INTEGRITY_IMPLEMENTED_VALIDATION_PENDING
```

The repository is the second LLM adapter and is internal to the StegVerse ecosystem. It is distinct from the SDK-facing adapter used with user-owned LLM accounts.

## Internal adapter mandate

```text
provider proposal
  -> canonical candidate normalization
  -> artifact integrity
  -> ingestion
  -> BCAT/GCAT admissibility at commit
  -> CGE monitoring and replay
  -> bounded receipt
  -> next governed boundary only
```

Human review is exception-only. It is not routine commit authority. The bridge remains non-executing and must not treat model generation, provider consensus, normalization, artifact integrity, or human review as admissibility.

## Ownership boundary

```text
StegVerse-SDK / user-account LLM adapter
  -> emit user/SDK-origin DECLARED candidates

hybrid-collab-bridge / internal LLM adapter
  -> emit and normalize internal ecosystem candidates
  -> validate candidate/route origin pairing
  -> preserve transition_id, run_id, event_id, and origin_manifest_id
  -> attach bridge and integrity evidence
  -> retarget only to Ecosystem-Delegation
  -> never self-grant execution, publication, delegation, or final-receipt authority

Ecosystem-Delegation
  -> evaluate governed delegation and authority references

master-records/orchestration
  -> lifecycle, final receipt, custody, reconstruction, Site index
```

## Installed governed normalization

```text
scripts/normalize_governed_transition_candidate.py
examples/sdk_transition_candidate.input.json
examples/llm_transition_candidate.input.json
examples/sdk_origin_hps_bridge_route.json
examples/llm_origin_hps_bridge_route.json
tests/test_governed_transition_normalization.py
.github/workflows/ci.yml
```

Validated evidence:

```text
Pull request: #4
Workflow: hybrid-bridge-ci
Run: 29167913108
Job: governed-normalization
Conclusion: success
```

Preserved invariants:

```text
transition_id unchanged
run_id unchanged
event_id unchanged
origin_manifest_id unchanged
candidate origin must match HPS route origin
next target becomes Ecosystem-Delegation
ALLOW_NEXT_BOUNDARY is not admissibility
```

## Documentation badge repair

Original failure:

```text
Workflow: docs-badge-sync
Run: 29187122775
Job: normalize-badges
First failing step: Ensure README badges
Failure location: split_badges() invocation
```

Repair:

```text
File: scripts/ensure_readme_badges.py
Repair commit: c4a305bf84cb25c8432251237d349500fbcfd867
```

Behavioral verification:

```text
Automated commit: 0af2d5d3425c3b0963a92ccad7e95a9895ba52c2
Author: StegVerse Bot
Message: docs(readme): normalize badges block
Result: repaired script successfully normalized and committed the README badge block
```

The bot-authored normalization commit is durable evidence that the repaired badge workflow reached its commit step. Badge repair is considered verified without changing normalization or authority behavior.

## API test repair installed

The legacy `api-tests` job ran `cd api && pytest -q tests` while `api/tests` contained no executable tests, producing an independently red job after successful dependency installation and compilation.

Installed bounded contract tests:

```text
api/tests/test_models.py
Commit: 1d04566abb6b42f6daef19ee91743fea35dfe0d8
Coverage:
  - human_gate defaults to false and remains exception-only
  - governed response states remain representable
  - denied output does not require a fabricated final artifact
```

Workflow validation of this repair remains pending.

## Artifact integrity contract installed

```text
api/app/governance/artifact_integrity.py
Commit: 8f21b9050ec04f3cf040046a5436ded4d5c45307

api/tests/test_artifact_integrity.py
Commit: dae1348963e4cce7d06f64957162e2597ecebf33
```

The contract is manifest-driven rather than README-specific. It:

```text
hashes candidate content with SHA-256
fails closed on empty content
returns NEEDS_REPAIR when declared required sections are missing
returns ALLOW_NEXT_BOUNDARY only when declared structural requirements are present
states explicitly that downstream admissibility remains pending
```

Artifact integrity does not diagnose semantic correctness, grant authority, execute, publish, delegate, or issue final receipts.

## Remaining files or modules to install

```text
StegVerse-Labs/hybrid-collab-bridge:
  - obtain green api-tests workflow evidence for commits 1d04566 and dae1348 or a later commit
  - wire artifact integrity into the internal proposal path before ingestion
  - add artifact manifest fields to the API request/response contract
  - replace remaining PAUSED_FOR_REVIEW conflation with explicit NEEDS_REPAIR, INTEGRITY_FAILED, ADMISSIBILITY_FAILED, and EXCEPTION_REVIEW states
  - emit bounded integrity evidence into CGE receipts

StegVerse-Labs/Ecosystem-Delegation:
  - normalized transition-candidate intake contract
  - bounded delegation result contract

master-records/orchestration:
  - observed workflow evidence record
  - transition_id and run_id lifecycle preservation record
```

## Next task

```text
1. Observe and record api-tests validation for the installed API and artifact-integrity tests.
2. Add artifact manifest declarations to RunRequest without granting execution authority.
3. Evaluate generated final output through artifact integrity before ingestion.
4. Return NEEDS_REPAIR or FAIL_CLOSED independently from BCAT/GCAT admissibility.
5. Attach integrity hash, missing-section evidence, and decision to CGE-monitored receipts.
6. Install normalized transition-candidate intake in Ecosystem-Delegation.
7. Preserve transition_id and run_id through delegation and final receipt.
```

## Permitted continuation scope

Permitted changes are bounded to deterministic parsing, tests, internal proposal normalization, artifact integrity, ingestion interfaces, admissibility status handling, CGE evidence, and receipts. Do not grant the bridge execution, publication, delegation, final-receipt, or cross-repository authority.

## Archive posture

This handoff preserves the internal-adapter distinction, completed normalization architecture, green normalization evidence, verified badge repair, API-test repair, artifact-integrity implementation, authority limits, pending validation, remaining installations, and exact continuation order. Earlier conversation context is not required.
