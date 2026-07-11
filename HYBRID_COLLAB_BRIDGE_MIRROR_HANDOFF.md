# Hybrid Collab Bridge Mirror Handoff

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Source of truth

This file is the current handoff and task source of truth for this repository.

## Current goal

```text
Goal: normalize sibling transition candidates into one governed next-boundary record
Phase: SDK-and-LLM-normalization-parity-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_VALIDATION_PENDING
```

## Architecture

```text
SDK candidate          \
LLM-adapter candidate   \
Site candidate           -> hybrid-collab-bridge normalization
External adapter        /            |
Manual review          /             v
                         StegVerse-Labs/Ecosystem-Delegation
                                      |
                                      v
                         master-records/orchestration
```

## Ownership boundary

```text
StegVerse-SDK / LLM-adapter
  -> emit origin-specific DECLARED candidates

hybrid-collab-bridge
  -> validate candidate/route origin pairing
  -> evaluate HPS route state
  -> preserve transition_id, run_id, event_id, and origin_manifest_id
  -> attach bridge decision evidence
  -> retarget only to Ecosystem-Delegation

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
```

Both sibling origins now use the same normalization implementation and relational contract.

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
```

## Next task

```text
1. Register normalization tests in the repository's existing validation surface without adding a workflow.
2. Observe validation evidence for both SDK and LLM normalization.
3. Pass normalized records to Ecosystem-Delegation.
4. Return bounded delegation results to master-records/orchestration.
```

## Archive posture

This handoff contains the current bridge architecture, parity implementation, authority limits, and next task. Earlier conversation context is not required.
