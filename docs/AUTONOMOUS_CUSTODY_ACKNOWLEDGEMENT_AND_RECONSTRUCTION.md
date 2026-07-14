# Autonomous Custody Acknowledgement and Reconstruction

The governed lifecycle now continues beyond custody intake without routine human queue handling.

## Installed master-record lifecycle controls

```text
master-records/orchestration
scripts/reconcile_custody_lifecycle.py
tests/test_custody_lifecycle.py
.github/workflows/reconcile-custody-lifecycle.yml
```

Accepted custody evidence is indexed by the stable composite identity:

```text
transition_id:run_id
```

The reconciler emits deterministic custody acknowledgements while preserving:

```text
candidate_id
custody_status
custody evidence path and SHA-256
admissibility_result = PENDING
commit_time_validity = PENDING
final_receipt_id = null
release_authority = false
```

Conflicting evidence for the same transition/run identity is recorded as a duplicate and is not silently substituted.

## Installed acknowledgement return path

```text
master-records/orchestration
scripts/transport_custody_acknowledgements.py
tests/test_custody_ack_transport.py
.github/workflows/transport-custody-acknowledgements.yml

StegVerse-Labs/Ecosystem-Delegation
scripts/reconcile_custody_acknowledgements.py
tests/test_custody_acknowledgements.py
.github/workflows/reconcile-custody-acknowledgements.yml
```

The transport is token-gated. Missing external transport authority produces a durable `BLOCKED_EXTERNAL_AUTHORITY` state with `manual_action_required=false`; credentials are never fabricated.

## Authority boundaries

```text
custody acknowledgement != final receipt
reconstruction index != present-time authority
received-uncommitted != admissible
transport completion != execution authority
duplicate detection != supersession authority
```

## Current autonomous lifecycle

```text
governed session
-> delegation candidate
-> HPS delegation evaluation
-> custody-bound result
-> master-record custody intake
-> reconstruction index
-> custody acknowledgement
-> token-gated acknowledgement return
-> upstream acknowledgement index
```

All routine validation, indexing, duplicate detection, evidence writing, state writing, and acknowledgement processing are scheduled or push-triggered.
