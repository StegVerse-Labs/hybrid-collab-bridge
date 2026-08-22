# Delegation Outbox Root Import Repair — 2026-08-22

## Observed failure

- repository: `StegVerse-Labs/hybrid-collab-bridge`
- branch: `main`
- workflow: `reconcile-delegation-outbox`
- run: `32548273364`
- job: `96970602373`
- failing main SHA: `6d05bee390af7885f161ef76addff0361cd0363d`
- failure step: `Validate candidate and outbox contracts`

The dependency installation succeeded, including `pytest`. Test collection then failed after the workflow changed directory into `api/` and `api/tests/test_delegation_outbox.py` attempted `from scripts.reconcile_delegation_outbox import reconcile`.

Observed failure class: `REPOSITORY_ROOT_IMPORT_HIDDEN_BY_WORKING_DIRECTORY`.

## Bounded repair

Branch `fix/delegation-outbox-root-import` keeps validation at repository root and runs with `PYTHONPATH=.:api`, preserving both repository-root `scripts` imports and `api/app` imports.

No delegation authority, provider authority, token handling, transport behavior, publication behavior, or downstream mutation contract is broadened.

## State

- source repair installed on branch: true
- pull request: `#16`
- hosted repair validation observed: false
- merged to main: false
- production reconciliation success observed: false

Do not equate this repair branch or pull request with completed reconciliation.