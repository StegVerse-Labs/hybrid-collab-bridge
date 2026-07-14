# Hybrid Collab Bridge Mirror Handoff

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Source of truth

This file is the current handoff and task source of truth for this repository.

## Current goal

```text
Goal: normalize sibling transition candidates into one governed next-boundary record
Phase: SDK-and-LLM-normalization-parity-validated
Result: GOVERNED_NORMALIZATION_GREEN
```

The repository is the second LLM adapter and is internal to the StegVerse ecosystem. It is distinct from the SDK-facing adapter used with user-owned LLM accounts.

## Internal adapter mandate

```text
provider proposal
  -> canonical candidate normalization
  -> ingestion
  -> BCAT/GCAT admissibility at commit
  -> CGE monitoring and replay
  -> bounded receipt
  -> next governed boundary only
```

Human review is exception-only. It is not the routine commit authority. The bridge must remain non-executing and must not treat model generation, referee output, normalization, or human review as admissibility.

## Architecture

```text
SDK candidate          \
LLM-adapter candidate   \
Site candidate           -> hybrid-collab-bridge normalization
External adapter        /            |
Manual exception review/             v
                         StegVerse-Labs/Ecosystem-Delegation
                                      |
                                      v
                         master-records/orchestration
```

## Ownership boundary

```text
StegVerse-SDK / user-account LLM adapter
  -> emit user/SDK-origin DECLARED candidates

hybrid-collab-bridge / internal LLM adapter
  -> emit and normalize internal ecosystem candidates
  -> validate candidate/route origin pairing
  -> evaluate HPS route state
  -> preserve transition_id, run_id, event_id, and origin_manifest_id
  -> attach bridge decision evidence
  -> retarget only to Ecosystem-Delegation
  -> never self-grant execution authority

Ecosystem-Delegation
  -> evaluate governed delegation and authority references

master-records/orchestration
  -> lifecycle, final receipt, custody, reconstruction, Site index
```

## Installed governed-candidate normalization

```text
scripts/normalize_governed_transition_candidate.py
examples/sdk_transition_candidate.input.json
examples/llm_transition_candidate.input.json
examples/sdk_origin_hps_bridge_route.json
examples/llm_origin_hps_bridge_route.json
tests/test_governed_transition_normalization.py
.github/workflows/ci.yml with separate governed-normalization and api-tests jobs
```

Both sibling origins use the same normalization implementation and relational contract.

Decision-to-lifecycle mapping:

```text
ALLOW_NEXT_BOUNDARY -> READY
REVIEW -> VERIFICATION_REQUIRED
DENY -> BLOCKED
FAIL_CLOSED -> FAIL_CLOSED
```

Output remains bounded:

```text
admissibility_result: PENDING
commit_time_validity: PENDING
action_ref: null
final_receipt_id: null
master_record_status: NOT_YET_SUBMITTED
```

## Preserved relational invariant

```text
transition_id unchanged
run_id unchanged
event_id unchanged
origin_manifest_id unchanged
candidate origin must match HPS route origin
bridge decision recorded as evidence
next target becomes Ecosystem-Delegation
```

## Non-authority rule

```text
The bridge does not execute.
The bridge does not publish.
The bridge does not grant authority.
ALLOW_NEXT_BOUNDARY is not admissibility.
Normalization is not final-receipt issuance.
Human review is not commit authority.
Provider consensus is not commit authority.
```

## Validation evidence

```text
Pull request: #4
Workflow: hybrid-bridge-ci
Run: 29167913108
Job: governed-normalization
Conclusion: success
Test command: python -m pytest -q tests/test_governed_transition_normalization.py
```

Observed green coverage:

```text
SDK candidate identity preservation and Ecosystem-Delegation routing
LLM candidate identity preservation and Ecosystem-Delegation routing
origin/route mismatch fail-closed behavior
```

The existing API test job remains independently red and is a separate repair task.

## Documentation badge failure and repair

Original failure evidence:

```text
Notification date: 2026-07-12
Branch: main
Commit: 6cec14059a8a8396c64be7bdd3a0a82139c437e2
Workflow: docs-badge-sync
Run: 29187122775
Job: normalize-badges
First failing step: Ensure README badges
Command: python3 scripts/ensure_readme_badges.py
Failure location: split_badges() invocation from main()
```

Bounded repair installed:

```text
File: scripts/ensure_readme_badges.py
Repair commit: c4a305bf84cb25c8432251237d349500fbcfd867
Change: replace newline-sensitive substitution with deterministic complete-badge extraction
Change: preserve canonical workflow ordering and one badge per line
Authority impact: none
Normalization impact: none
```

No workflow run was associated with the repair commit when first queried. Verification remains pending and must be recorded here when observed.

## Remaining files or modules to install

```text
StegVerse-Labs/hybrid-collab-bridge:
  - verify docs-badge-sync after commit c4a305b or a later commit
  - repair the pre-existing api-tests job under its separate task
  - add proposal/artifact integrity contract for internal LLM output
  - replace routine human_gate semantics with automated admissibility/integrity states
  - connect normalized proposals to ingestion, BCAT/GCAT, and CGE interfaces

StegVerse-Labs/Ecosystem-Delegation:
  - normalized transition-candidate intake contract
  - bounded delegation result contract

master-records/orchestration:
  - observed workflow evidence record
  - transition_id and run_id lifecycle preservation record
```

## Next task

```text
1. Verify docs-badge-sync on repair commit c4a305b or a later commit and record the run result.
2. Repair the legacy bridge API test failure without changing normalization authority boundaries.
3. Define the internal-adapter proposal and artifact-integrity contracts.
4. Replace human-review-default behavior with automatic integrity/admissibility status handling; retain human review only as an exception route.
5. Install normalized transition-candidate intake in Ecosystem-Delegation.
6. Return bounded delegation results to master-records/orchestration.
7. Preserve transition_id and run_id through delegation and final receipt.
```

## Permitted continuation scope

Permitted changes are bounded to deterministic parsing, tests, internal proposal normalization, artifact integrity, ingestion interfaces, admissibility status handling, CGE evidence, and receipts. Do not grant the bridge execution, publication, delegation, final-receipt, or cross-repository authority.

## Archive posture

This handoff preserves the internal-adapter distinction, completed normalization architecture, green evidence, authority limits, badge-repair commit, pending verification, remaining installations, and exact continuation order. Earlier conversation context is not required after this file is verified.