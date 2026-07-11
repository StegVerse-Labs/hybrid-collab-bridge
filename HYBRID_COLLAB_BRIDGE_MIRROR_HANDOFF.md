# Hybrid Collab Bridge Mirror Handoff

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Source of truth

This file is the current handoff and task source of truth for this repository.

## Current goal

```text
Goal: normalize sibling transition candidates into one governed next-boundary record
Phase: SDK normalization installed; LLM parity and delegation integration next
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
  -> validate origin/route pairing
  -> evaluate HPS route state
  -> preserve transition_id, run_id, event_id, and origin_manifest_id
  -> attach bridge decision evidence
  -> retarget only to Ecosystem-Delegation

Ecosystem-Delegation
  -> evaluate governed delegation and authority references

master-records/orchestration
  -> lifecycle, final receipt, custody, reconstruction, Site index
```

## Installed HPS bridge files

```text
docs/HPS_ROUTE_BRIDGE.md
schemas/hps.bridge.route.schema.json
examples/sdk_origin_hps_bridge_route.json
examples/llm_origin_hps_bridge_route.json
examples/expired_hps_bridge_route.json
scripts/verify_hps_bridge_route.py
tests/test_hps_bridge_route.py
receipts/hps_bridge_activation_receipt.json
```

## Installed governed-candidate normalization

```text
scripts/normalize_governed_transition_candidate.py
examples/sdk_transition_candidate.input.json
tests/test_governed_transition_normalization.py
```

The normalizer maps bridge decisions to lifecycle posture:

```text
ALLOW_NEXT_BOUNDARY -> READY
REVIEW -> VERIFICATION_REQUIRED
DENY -> BLOCKED
FAIL_CLOSED -> FAIL_CLOSED
```

It does not convert bridge output into admissibility or execution authority. Output remains:

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
The bridge prepares a bounded record for the next governed boundary.
```

## Next task

```text
1. Add and verify LLM-adapter candidate normalization parity.
2. Register normalization checks in the repository's existing validation surface without adding a workflow.
3. Read ECOSYSTEM_DELEGATION_MIRROR_HANDOFF.md.
4. Install delegation-decision references while preserving transition_id and run_id.
5. Return the bounded decision record to master-records/orchestration for lifecycle enrichment.
```

## Archive posture

This handoff contains the current bridge architecture, installed normalization files, authority limits, and next task. Earlier conversation context is not required.
