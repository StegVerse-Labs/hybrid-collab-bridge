# Autonomous Queue Reconciliation

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Purpose

Remove routine manual handling between governed runtime traces, bridge delegation candidates, Ecosystem-Delegation intake, and master-record custody intake.

## Source outbox

```text
scripts/reconcile_delegation_outbox.py
api/tests/test_delegation_outbox.py
.github/workflows/reconcile-delegation-outbox.yml
```

The source reconciler scans governed `03_referee.json` session traces and emits deterministic candidates under:

```text
outbox/ecosystem-delegation/
```

It writes:

```text
state/delegation_outbox_reconciliation.json
```

Invalid traces are recorded in machine-readable skipped evidence. They do not create a human task.

## Ecosystem-Delegation inbox

```text
StegVerse-Labs/Ecosystem-Delegation
scripts/reconcile_hcb_delegation_inbox.py
tests/test_hcb_delegation_inbox.py
.github/workflows/reconcile-hcb-delegation-inbox.yml
```

Delivered records under:

```text
inbox/hybrid-collab-bridge/
```

are validated automatically. Accepted and failed-closed evidence is committed under:

```text
evidence/hcb-delegation-intake/
state/hcb_delegation_inbox_reconciliation.json
```

## Master-record custody inbox

```text
master-records/orchestration
scripts/reconcile_delegation_bound_transition_inbox.py
tests/test_delegation_bound_transition_inbox.py
.github/workflows/reconcile-delegation-bound-transition-inbox.yml
```

Delivered records under:

```text
inbox/ecosystem-delegation/
```

are reconciled automatically into custody acceptance or quarantine evidence under:

```text
evidence/delegation-bound-transition-intake/
state/delegation_bound_transition_inbox_reconciliation.json
```

## Authority posture

```text
outbox creation != transmission authority
inbox acceptance != delegation authority
delegation evaluation != execution authority
custody acceptance != release authority
custody acceptance != final receipt
workflow success != BCAT/GCAT admissibility
```

## Manual-task posture

Queue generation, queue scanning, validation, evidence generation, state writing, and repository-local commits are scheduled and push-triggered.

```text
manual_action_required = false
```

Cross-repository transport itself remains an authorized transport concern. These contracts do not fabricate credentials or silently grant one repository mutation authority over another. When authorized transport is present, no operator handling is required at either inbox.
