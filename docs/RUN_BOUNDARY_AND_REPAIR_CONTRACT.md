# Internal Run Boundary and Repair Candidate Contract

Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Purpose

This record extends `HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md` with the next bounded internal-adapter controls.

## Installed run-boundary policy

```text
api/app/governance/run_boundary.py
Commit: 1837bebde4c47151fc8bc1a76d593b7a99926c0a
```

The policy deterministically separates:

```text
provider denial -> ADMISSIBILITY_FAILED
provider defer -> EXCEPTION_REVIEW
allowed + no integrity evidence -> INTEGRITY_FAILED
allowed + empty artifact -> INTEGRITY_FAILED
allowed + missing declared sections -> NEEDS_REPAIR
allowed + integrity pass -> OK
explicit human exception request -> EXCEPTION_REVIEW
```

Only `OK` permits accepted-result ingestion. Denied, deferred, failed-integrity, and repair-required candidates remain observable governance events but are not accepted run results.

## Direct boundary tests

```text
api/tests/test_run_boundary.py
Commit: 9f099d31277319258cc1d63d3b8ee432080f0b25
```

Coverage proves:

- a complete allowed artifact may enter accepted-result ingestion;
- an incomplete allowed artifact cannot enter accepted-result ingestion;
- an empty allowed artifact fails closed;
- denial remains observable but is not an accepted result;
- deferment routes only to exception review;
- human review cannot become commit authority;
- integrity ledger evidence preserves hash, manifest, missing sections, decision, and downstream-admissibility pending state.

## Runtime CGE event installation path

```text
scripts/install_run_boundary_cge_event.py
Initial commit: 7f0e1ed4cc31ce8e804c080de86cc5c6feaea0df
Trigger revision: 376ba99cac26ce06607b9363b92dc80746d3fe59

.github/workflows/install-run-boundary-cge-event.yml
Commit: 169144d2b9db3f1d9cbceaa953a7a226ee5c5cae
```

The installer is bounded to `api/app/main.py`. It is designed to:

1. replace duplicated inline status logic with the deterministic run-boundary policy;
2. gate accepted-result StegDB ingestion on `may_ingest_accepted_result`;
3. emit a dedicated CGE `observe` ledger event for artifact-integrity evaluation;
4. include run identity, artifact identity, content SHA-256, declared sections, missing sections, integrity decision, run status, and downstream-admissibility pending state;
5. include the integrity-event receipt in the session trace without treating it as a final receipt.

Runtime installation remains pending until an automated commit modifies `api/app/main.py` and is read back.

## Repair-candidate contract

```text
api/app/governance/repair_candidate.py
Commit: 29aa2b64d6e9311b93f034015ccb286f1a4adcec

api/tests/test_repair_candidate.py
Commit: 8e5ebaa15ba728018854140d8e51a787efea9a8d
```

A repair candidate:

- is created only from `NEEDS_REPAIR` or `FAIL_CLOSED` evidence;
- preserves the original run ID, artifact ID, and content SHA-256;
- receives a deterministic repair-candidate ID;
- remains `DECLARED` with admissibility and commit-time validity `PENDING`;
- has no action reference and no final receipt;
- does not overwrite the original artifact;
- does not execute repair work or grant authority.

## Non-authority invariant

```text
Run-boundary classification is not BCAT/GCAT admissibility.
Integrity observation is not final-receipt issuance.
Repair declaration is not repair execution.
Human exception review is not commit authority.
The bridge does not execute, publish, delegate, or issue final receipts.
```

## Next continuation

1. Observe the automated `api/app/main.py` installation commit and read it back.
2. Record green bounded tests or exact failure evidence.
3. Wire repair-candidate declaration into `NEEDS_REPAIR` and `INTEGRITY_FAILED` traces without automatic execution.
4. Add the normalized transition-candidate intake contract to `StegVerse-Labs/Ecosystem-Delegation`.
5. Preserve transition and run identities through delegation and master-record lifecycle custody.
