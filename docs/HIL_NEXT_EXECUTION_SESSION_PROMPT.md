# HIL Qualified Recognition — Next Execution Session Prompt

Use the connected GitHub repositories directly and continue `HIL-QUALIFIED-RECOGNITION-ACTIVATION-001`.

Treat live repository state, Git history, workflow runs, jobs, logs, artifacts, committed evidence, immutable blobs, admission receipts, and custody receipts as authoritative over prior chat claims.

## Read first

1. `HIL_MIRROR_HANDOFF.md`
2. `docs/HIL_QUALIFIED_RECOGNITION_LAYER.md`
3. `schemas/hil-qualified-recognition.schema.json`
4. `evidence/hil/HIL-TRACE-0001-qualified-recognition-candidate.json`
5. `scripts/validate_hil_qualified_recognition.py`
6. `.github/workflows/hil-qualified-recognition-validate.yml`
7. `evidence/hil/HIL-TRACE-0001-hosted-validation-observation.json`
8. `evidence/hil/HIL-TRACE-0001-admission-request-candidate.json`

## Current determination

The layer is **being built**. Contract, schema, bounded candidate, validator, positive and negative fixtures, and a hosted validation/replay workflow are committed. It is not activated.

Hosted evidence remains unresolved. The observed commit-run query returned no pull-request-associated run, but that connector result cannot determine whether a push-triggered or manually dispatched run occurred. Do not infer success or failure from absence.

## Execute in order

1. Resolve the authoritative hosted run for `.github/workflows/hil-qualified-recognition-validate.yml` after commit `14e255231c72c8b7e61da43c8db811d4061a4ed2` or a later relevant commit.
2. Record run ID, attempt, event, head SHA, job ID, terminal conclusion, every step outcome, and complete logs.
3. Fetch the `hil-qualified-recognition-validation` artifact and record artifact ID, digest, byte size, expiry, and exact hashes of both receipt files.
4. Repair only a defect proven by hosted logs. Repeat until one green hosted run is evidenced.
5. Commit immutable validation and replay receipts. Require byte identity across the two replay executions.
6. Update `evidence/hil/HIL-TRACE-0001-admission-request-candidate.json` with input hashes and change submission posture only after hosted preconditions are satisfied.
7. Read the authoritative `*_MIRROR_HANDOFF.md` in the selected `GCAT-BCAT-Engine` admission repository before mutation. Submit a bounded admission request and require `ALLOW`, `DENY`, or `ERROR` without authority expansion.
8. After `ALLOW`, resolve the Master Records authority from its own mirror handoff and preserve exact bytes, hashes, source commit, admission decision, custody event, supersession posture, and standing history.
9. Issue an activation receipt only when every criterion in `HIL_MIRROR_HANDOFF.md` is evidenced.
10. Only after activation, coordinate publication verification for `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Fail-closed rules

- No hosted run evidence means no validation claim.
- No green validation and replay evidence means no admission submission.
- No `ALLOW` means no admitted standing.
- No custody receipt means no activation.
- No activation receipt means no publication or release claim.

## Archive rule

The source conversation is not required after this prompt and the mirror handoff are committed. A continuing session must work from repository evidence only.
