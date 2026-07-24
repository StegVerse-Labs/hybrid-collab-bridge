# Automatic Human–LLM Assessment Activation

Status: IMPLEMENTED — CI OBSERVATION PENDING
Updated: 2026-07-24
Repository: `StegVerse-Labs/hybrid-collab-bridge`

## Activated path

Every successful `POST /v1/run` response is now intercepted by the governed run-assessment hook.

The hook:

1. reads the original run request without removing it from the downstream request stream;
2. allows a complete `interoperability_assessment` object to accompany the run;
3. otherwise constructs an evidence-bounded baseline assessment;
4. marks unsupported semantic tests `INDETERMINATE` rather than inferring success from fluent output;
5. submits the assessment through the canonical Human–LLM assessment runtime;
6. applies structural validation and canonical BCAT/GCAT admission;
7. writes `04_human_llm_pair_assessment.json` into the session directory;
8. returns the governed assessment result in the `/v1/run` response under `interoperability`;
9. denies governed publication unless the combined decision is `allow`;
10. returns a fail-closed interoperability result if attachment itself fails.

## Default evidence posture

A generated answer does not independently establish:

- meaning preservation;
- vocabulary alignment;
- boundary control;
- contradiction detection;
- evidence classification;
- audit-gap control;
- review comprehension;
- revision integrity;
- independent reconstruction.

Therefore, an ordinary run without supplied assessment evidence receives an automatic `INDETERMINATE` baseline and cannot be treated as publication-admissible.

This is intentional. Automatic assessment attachment does not mean automatic approval.

## Startup integration

The governance package is imported before `main.py` constructs the FastAPI application. Its bootstrap now:

- supplies the environment-derived `ADMIN_TOKEN` fallback needed by the existing legacy initialization order;
- installs the run-assessment middleware exactly once when the Hybrid Collab Bridge application is constructed.

This avoids a second manual assessment call while preserving the existing central application file.

## Implemented files

- `api/app/governance/human_llm_run_hook.py`
- `api/app/governance/__init__.py`
- `tests/test_human_llm_run_hook.py`
- `.github/workflows/human-llm-interoperability.yml`

## Tests added

The test suite now verifies:

- automatic baselines remain fail-closed;
- supplied assessments are preserved as independent copies;
- middleware installation is idempotent;
- successful `/v1/run` responses contain an interoperability result;
- authentication tokens are forwarded to canonical assessment submission;
- automatic reviewer action is recorded.

## Remaining obligations

- Observe a successful GitHub Actions run for the activation tranche.
- Add complete live `/v1/run` fixtures against the actual provider and embedded CGE stack.
- Add canonical examples showing supplied `PASS`, `PARTIAL`, `FAIL`, and `INDETERMINATE` run assessments.
- Add signer identity, signature, and key-reference fields when the canonical receipt contract exposes them.
- Review `StegVerse-Labs/Site/docs/SITE_MIRROR_HANDOFF.md` before public mirroring.
- Verify Publisher, admissibility-wiki, and stegguardian-wiki synchronization at release readiness.
