# Hybrid Collab Bridge Mirror Handoff

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Source of truth

This file is the current handoff and task source of truth for this repository.

## Current goal

```text
Goal: govern internal LLM proposals through deterministic normalization and artifact integrity before the next ecosystem boundary
Phase: internal-adapter-integrity-runtime-wired
Result: NORMALIZATION_GREEN_INTEGRITY_ENFORCED_BEFORE_INGESTION
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

```text
Original run: 29187122775
Original failure: split_badges() invocation
Repair file: scripts/ensure_readme_badges.py
Repair commit: c4a305bf84cb25c8432251237d349500fbcfd867
Behavioral verification commit: 0af2d5d3425c3b0963a92ccad7e95a9895ba52c2
Behavioral result: StegVerse Bot normalized and committed the README badge block
```

Badge repair is verified without changing normalization or authority behavior.

## API and artifact-integrity contracts

```text
api/app/models.py
  Commit: 548356cf7e2dd353082fef65bac430da4816c315
  Adds ArtifactManifest, IntegrityEvidence, and explicit governed statuses

api/app/governance/artifact_integrity.py
  Commit: 8f21b9050ec04f3cf040046a5436ded4d5c45307

api/tests/test_artifact_integrity.py
  Commit: dae1348963e4cce7d06f64957162e2597ecebf33

api/tests/test_models.py
  Initial repair commit: 1d04566abb6b42f6daef19ee91743fea35dfe0d8
  Expanded contract commit: 212ccba5d679912b4412028faf93036c003f8ea7
```

The integrity contract is manifest-driven. It hashes candidate content, fails closed on empty content, returns `NEEDS_REPAIR` for missing declared sections, and returns `ALLOW_NEXT_BOUNDARY` only when declared structural requirements are present.

Artifact integrity does not diagnose semantic correctness, grant authority, execute, publish, delegate, or issue final receipts.

## Runtime integrity wiring

Installed files and commits:

```text
scripts/install_internal_artifact_integrity_wiring.py
  Commit: 7aeb60ac041e65ee3e9e35d3217c234ed872ed2b
  Trigger revision: 1e1de36f9b32d71126b351875cc1d6f6cdb08be8

.github/workflows/install-internal-artifact-integrity.yml
  Commit: 8e8463ee8bf27363f556ab48dc440adf1fd5bdb3

api/app/main.py
  Automated install commit: 883f33c7a09eeb45a4b032b49d74312888d68260
  Author: StegVerse Bot
```

The one-shot installer workflow compiled the governed API and ran the bounded model and artifact-integrity tests before creating the automated runtime-wiring commit. The bot commit is durable evidence that those pre-commit steps completed successfully.

The `/v1/run` path now:

```text
extracts admitted final output
  -> evaluates declared artifact requirements
  -> emits SHA-256 and missing-section evidence
  -> blocks accepted-candidate ingestion on NEEDS_REPAIR or FAIL_CLOSED
  -> attaches bounded integrity evidence to the copied receipt and trace
  -> returns explicit status independently from BCAT/GCAT admission
```

Status separation now includes:

```text
ADMISSIBILITY_FAILED
INTEGRITY_FAILED
NEEDS_REPAIR
EXCEPTION_REVIEW
OK
```

Denied and deferred governance receipts may still be monitored as governance events. An allowed candidate cannot enter StegDB as an accepted run result unless artifact integrity passes.

## Non-authority rule

```text
The bridge does not execute.
The bridge does not publish.
The bridge does not grant delegation authority.
The bridge does not issue final receipts.
Provider admission is not artifact integrity.
Artifact integrity is not BCAT/GCAT admissibility.
Human review is not commit authority.
Provider consensus is not commit authority.
```

## Remaining files or modules to install

```text
StegVerse-Labs/hybrid-collab-bridge:
  - add direct endpoint tests proving failed integrity does not invoke accepted-candidate StegDB ingestion
  - emit a dedicated CGE ledger event for integrity evaluation rather than only embedding evidence in the copied final receipt
  - define automated repair-loop candidate creation without granting execution authority
  - remove or formally deprecate legacy PAUSED_FOR_REVIEW, DENIED, and DEFERRED response aliases after receipt migration review

StegVerse-Labs/Ecosystem-Delegation:
  - normalized transition-candidate intake contract
  - bounded delegation result contract

master-records/orchestration:
  - observed workflow evidence record
  - transition_id and run_id lifecycle preservation record
  - integrity evidence custody and reconstruction mapping
```

## Next task

```text
1. Add direct run-boundary tests for ALLOW, NEEDS_REPAIR, FAIL_CLOSED, ADMISSIBILITY_FAILED, and EXCEPTION_REVIEW.
2. Prove that an allowed but structurally incomplete artifact is not ingested as an accepted run result.
3. Emit a bounded CGE integrity-evaluation ledger event containing hash, manifest, missing sections, and decision.
4. Define the repair-candidate contract and preserve the original artifact hash and run identity.
5. Install normalized transition-candidate intake in Ecosystem-Delegation.
6. Return bounded delegation results to master-records/orchestration.
7. Preserve transition_id and run_id through delegation and final receipt.
```

## Permitted continuation scope

Permitted changes are bounded to deterministic parsing, tests, internal proposal normalization, artifact integrity, ingestion interfaces, admissibility status handling, CGE evidence, repair candidates, and receipts. Do not grant the bridge execution, publication, delegation, final-receipt, or cross-repository authority.

## Archive posture

This handoff preserves the internal-adapter distinction, completed normalization architecture, green normalization evidence, verified badge repair, API and integrity contracts, runtime pre-ingestion enforcement, authority limits, remaining installations, and exact continuation order. Earlier conversation context is not required.
