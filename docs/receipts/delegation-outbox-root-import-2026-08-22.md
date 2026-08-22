# Delegation Outbox Root Import Repair — 2026-08-22

## Observed main failure

- repository: `StegVerse-Labs/hybrid-collab-bridge`
- branch: `main`
- workflow: `reconcile-delegation-outbox`
- run: `32548273364`
- job: `96970602373`
- failing main SHA: `6d05bee390af7885f161ef76addff0361cd0363d`
- failure step: `Validate candidate and outbox contracts`

The dependency installation succeeded, including `pytest`. Test collection then failed after the workflow changed directory into `api/` and `api/tests/test_delegation_outbox.py` attempted `from scripts.reconcile_delegation_outbox import reconcile`.

Observed failure class: `REPOSITORY_ROOT_IMPORT_HIDDEN_BY_WORKING_DIRECTORY`.

## First bounded repair and hosted evidence

PR `#16` initially kept validation at repository root and set `PYTHONPATH=.:api` for the contract-validation step.

Hosted branch run `32548505262`, job `96971194104`, proved that repair:

- dependency installation: PASS;
- candidate/outbox contract validation: PASS;
- `9 passed in 0.28s`;
- next step `Reconcile governed session traces into outbox`: FAILED.

The next failure was another manifestation of the same path contract: `scripts/reconcile_delegation_outbox.py` imports `api.app.governance.delegation_candidate`, but the execution step did not inherit the root/API `PYTHONPATH` contract.

## Current bounded repair

Commit `ce8bcbf0256e6d6c84512bb156a4f3cd35bfb8c6` moves `PYTHONPATH=.:api` to the reconciliation job environment so both validation and execution share one deterministic import boundary.

No delegation authority, provider authority, token handling, transport behavior, publication behavior, or downstream mutation contract is broadened.

## State

- original contract-test import defect: hosted-validated repaired on branch
- reconciliation execution import defect: source repair installed on branch
- pull request: `#16`
- latest repair hosted validation observed: false
- merged to main: false
- production reconciliation success observed: false

Do not equate this repair branch or pull request with completed reconciliation.