# Hybrid Collaboration Bridge Mirror Handoff

_Last updated: 2026-06-18_

## Purpose

This handoff is the active task source of truth for `StegVerse-Labs/hybrid-collab-bridge`. It mirrors the Site/Publisher handoff pattern for a non-Site repository and is intended to let any later session resume the bridge work without needing the full chat history.

## Repository

- Organization: `StegVerse-Labs`
- Repository: `hybrid-collab-bridge`
- Default branch: `main`
- Visibility: public
- Current role: governed internal ecosystem adapter for API orchestration, BCAT/GCAT admission, and CGE-monitored traces.

## Current Status

### Confirmed from repository state

- The repository exists under `StegVerse-Labs/hybrid-collab-bridge` and is on default branch `main`.
- The README describes the bridge as a governed internal ecosystem adapter using API orchestration, BCAT/GCAT admission, and CGE-monitored traces.
- The README defines the high-level execution path as `PROPOSE -> ADMIT (BCAT/GCAT) -> EXECUTE -> PROVE -> RECEIPT`.
- The README lists the bridge endpoints `/health`, `/v1/run`, and `/v1/continue` as the primary operational surface.
- The generated workflow status document currently reports 19 workflows with workflow dispatch, 0 no-dispatch workflows, and 0 broken YAML workflows. Treat this as syntax/readiness status only, not live functional proof.

### Confirmed from recent run screenshots

Recent GitHub Actions screenshots showed live-run failures even though workflow syntax was normalized:

1. `GH_TOKEN` / GitHub CLI auth conflict:
   - Symptom: `The value of the GH_TOKEN environment variable is being used for authentication. To have GitHub CLI store credentials instead, first clear the value from the environment.`
   - Status: v2 workflow replacements removed `gh auth login --with-token` calls because GitHub CLI already reads `GH_TOKEN`.

2. Shell `unexpected end of file` failures:
   - Symptom: failed shell blocks during comment/body handling.
   - Status: v2 workflow replacements moved PR/issue comments to file-based body handling (`--body-file`) instead of fragile multiline shell variables.

3. Badge sync shell syntax failure:
   - Symptom: `syntax error: unexpected end of file` in the commit step.
   - Status: v2 badge workflow replacement normalized embedded Python and commit handling.

## TV/TVC credential-model consistency correction — 2026-08-26

Current source inspection found that the bridge's provider registry and `api/app/governance/tv_tvc.py` still implement a **consumer-side secret delivery model**:

```text
TVCClient -> EphemeralCredential.token -> bridge process
bridge cache -> provider adapter token injection -> external provider
optional file/env credential modes
optional direct environment fallback
```

The provider classes also retain direct environment reads such as `OPENAI_API_KEY` and construct provider authorization headers in the bridge process.

That source model is **not current production credential authority** under the governing TV/TVC policy. Current authority requires credential-bearing production processing to remain inside a TV/TVC-owned processing boundary; storage location does not confer authority and consumer repositories may receive only bounded non-secret results/receipts/capability outputs.

Canonical governing evidence:

```text
StegVerse-Labs/TV/docs/TV_MIRROR_HANDOFF.md
StegVerse-Labs/TV/policies/external_secret_processing_authority_policy.json
StegVerse-Labs/TVC/docs/CREDENTIAL_MODEL_CONSISTENCY_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/TVC_THIRD_PARTY_CREDENTIAL_INTR_SKAP_PROTOCOL.md
StegVerse-Labs/TVC/coordination/credential-consumer-risk-scan.v1.json
```

Current classification:

```text
direct provider env-secret source: IMPLEMENTED_SOURCE / NOT AUTHORIZED AS CURRENT PRODUCTION CREDENTIAL PATH
TVCClient token-return/cache model: CONTRADICTORY_WITH_CURRENT_PRODUCTION_PROCESSING_BOUNDARY
live runtime use of those paths: NOT PROVEN BY THIS REVIEW
bridge credential authority: NONE
TV/TVC credential authority: PRESERVED
provider output authority: NONE / advisory
```

Until the TV/TVC credential consistency audit closes and this repository is reconciled against it:

- do not activate a provider by adding/reusing raw API secrets in this bridge;
- do not treat `TVC_MODE=env`, local vault files, direct token return, token cache, or env fallback as a production credential path;
- do not create a second credential broker or new Vault here;
- credential-bearing external-provider execution must reuse the existing TV/TVC provider-operation / admitted-route architecture;
- credential-free local/mock validation may continue.

This correction does not invalidate historical workflow repair evidence and does not claim that any protected credential was exposed in a live run.

## Active Goal

Stabilize the hybrid-collab-bridge workflows so the bridge can reliably:

1. Run manual and comment-triggered AI review jobs.
2. Fetch PR diff or repo context safely.
3. Call the selected model provider.
4. Post output back to the PR, issue, or bridge issue.
5. Preserve workflow-status documentation without shell/YAML fragility.
6. Keep external model output treated as untrusted review material, not authority.

## Done Definition

The current goal is done when all of the following are true:

- `bridge-openai.yml` completes a manual self-check run.
- `bridge-github-models.yml` completes a manual self-check run.
- `stegverse-ai-entity.yml` completes a manual self-check run.
- `stegverse-claude-entity.yml` reaches the provider call step without GitHub CLI auth failure; provider-specific failures must be explicit missing/invalid secret failures, not YAML/shell failures.
- `workflows-status-badges.yml` completes and either commits updated docs or exits with `No changes to commit.`
- No workflow run fails because of `gh auth login`, multiline `GITHUB_OUTPUT`, or shell EOF errors.
- A short status note is committed or written to docs after successful validation.

## Current Build Notes

### Files already repaired in the working bundle

The current repaired set is the v2 replacement bundle:

- `bridge-openai.yml`
- `bridge-github-models.yml`
- `stegverse-ai-entity.yml`
- `stegverse-claude-entity.yml`
- `workflows-status-badges.yml`

Key repair rules used:

- Do not run `gh auth login` when `GH_TOKEN` is set.
- Use `GH_TOKEN` as the GitHub CLI auth source directly.
- Write model output to Markdown files and post with `gh pr comment --body-file` or `gh issue comment --body-file`.
- Keep fetched diff context in files, not shell-expanded multiline variables.
- Avoid raw heredoc structures that can be broken by nested Markdown fences or YAML indentation.

## Roadmap

### Phase 1 — Workflow stabilization

Status: in progress.

Tasks:

1. Confirm v2 replacements are present in the repository.
2. Run manual dispatch for each of the five repaired workflows.
3. Capture the first failing step if any provider secret is absent or invalid.
4. Separate infrastructure failures from expected provider-secret failures.
5. Update workflow status docs after live validation.

Exit criteria:

- No syntax, EOF, or GitHub CLI auth failures remain.
- Each workflow either succeeds or fails only at a clearly expected external-provider boundary.

### Phase 2 — Bridge safety boundary

Status: next.

Tasks:

1. Add a bridge request envelope that separates:
   - public-safe context,
   - repo metadata,
   - PR diff excerpt,
   - human instruction,
   - redaction notes.
2. Add explicit deny rules for:
   - secrets,
   - tokens,
   - private deployment hooks,
   - unpublished formalism internals,
   - privileged StegVerse architecture not already public.
3. Treat all model responses as untrusted review output.
4. Add minimal receipt metadata to every posted model response.

Exit criteria:

- Every external model call passes through a visible context boundary.
- Every response is labeled as advisory and non-authoritative.

### Phase 3 — Admission and receipt proof

Status: planned.

Tasks:

1. Add a lightweight receipt JSON artifact for every model invocation.
2. Include provider, model, target repo, PR number, instruction hash, context hash, and response hash.
3. Persist receipt artifacts using GitHub Actions artifacts first.
4. Later mirror receipts to CGE Light when the repo-local engine is wired.

Exit criteria:

- A reviewer can reconstruct what context was sent, which provider was used, and what output was posted without exposing secrets.

### Phase 4 — Provider expansion

Status: blocked until Phases 1-3 are stable.

Candidate providers:

- OpenAI API
- GitHub Models
- Claude / Anthropic
- Kimi / Moonshot, public-safe critique only
- local/mock provider for no-secret testing

Rule:

Provider expansion must not happen before the redaction/admission boundary exists.

### Phase 5 — Ecosystem integration

Status: future.

Integration candidates:

1. StegCore admissibility examples.
2. Site/Publisher paper display checks.
3. Token Vault / TVC credential reference flow.
4. CGE Light receipt ingestion.
5. Public proof page showing bridge safety and evidence flow.

## Risk Register

| Risk | Severity | Status | Mitigation |
|---|---:|---|---|
| External LLM receives private StegVerse architecture | High | open | Add public-safe context envelope and deny list |
| GitHub CLI auth conflict | Medium | repaired in v2 | Remove `gh auth login`; rely on `GH_TOKEN` |
| Shell EOF from multiline model output | Medium | repaired in v2 | Use file-based output and `--body-file` |
| Workflow docs report syntax OK but live runs still fail | Medium | open | Distinguish syntax scan from live validation |
| Provider-specific secrets missing | Low/expected | open | Treat as provider boundary, not workflow failure |

## Immediate Next Steps

1. Confirm v2 workflow replacements are committed in the repository.
2. If not committed, apply them directly to the five workflow files.
3. Re-run:
   - `workflows-status-badges.yml`
   - `bridge-github-models.yml`
   - `bridge-openai.yml`
   - `stegverse-ai-entity.yml`
   - `stegverse-claude-entity.yml`
4. Record live run outcome in this handoff.
5. Begin Phase 2 redaction/admission envelope only after Phase 1 stops failing for shell/auth reasons.

## Completion Estimate

- Organization: StegVerse-Labs — 62% complete for this bridge-stabilization goal.
- Repository: hybrid-collab-bridge — 68% complete for current workflow stabilization.
- Activation: hybrid-collab-bridge is 55% complete to goal activation because syntax normalization is present, but live run proof and safety-envelope work remain.
- Fully developed files vs scaffolding/stubs: 60% complete. The README, workflow set, and status docs are developed enough to operate, but external-model safety boundary and receipt persistence still need implementation proof.
- Delta: `hybrid-collab-bridge: actual 55% vs built 68%` — built artifacts are ahead of verified activation because screenshots showed live-run failures after syntax repairs, and live reruns have not yet been confirmed clean.

## Archive Readiness

This handoff is intended to replace reliance on the chat thread for bridge work. Future sessions should begin here, then inspect live workflow runs before making new architectural changes.


## Issue #14 provider credential-boundary source retirement — 2026-08-26/27

The active replacement lane from `hybrid-collab-bridge#14` has now advanced from containment-only to a bounded source repair.

Implemented on branch `fix/issue14-tvc-provider-boundary`:

```text
api/app/governance/tv_tvc.py
  historical secret-return/cache/file/env/direct model: RETIRED
  compatibility surface: NON_SECRET / FAIL_CLOSED
  raw or ephemeral provider credential returned to bridge: FALSE

api/app/registry.py
  TVC_MODE consumer credential wrapping: REMOVED
  bridge-local credential adapter injection: REMOVED

external provider adapters:
  OpenAI
  Anthropic
  Gemini
  DeepSeek
  Grok
  Kimi
  Perplexity
```

All seven external adapters now instantiate without reading provider secrets and return:

```text
state: BLOCKED
error: TVC_ADMITTED_PROVIDER_ROUTE_REQUIRED
credential_material_present: false
provider_execution_performed: false
authority_effect: false
```

They perform no provider network call in this source state.

Local/mock provider classes are not removed by this repair. This preserves credential-free local validation while preventing the bridge from becoming a provider credential processor.

The legacy class names `TVCClient`, `TVProviderAdapter`, and `EphemeralCredential` remain only as compatibility surfaces. `EphemeralCredential` has no token field, the client returns no protected value, and the adapter cannot inject credentials.

Regression coverage is retained in the existing `api/tests/test_tv_tvc.py` lane and explicitly rejects:
- TV vault-file reads;
- environment-secret fallback;
- direct TVC unseal calls returning credentials;
- token injection/caching;
- direct provider API-key reads;
- direct provider network execution.

Current state:

```text
issue #14 source replacement: IMPLEMENTED_ON_BRANCH
hosted CI validation: PENDING
merge: PENDING
provider credential authority in bridge: NONE
TV/TVC credential authority: PRESERVED
admitted external provider route into bridge: NOT IMPLEMENTED HERE / EXISTING OWNER REQUIRED
external provider execution from this repair: NOT EXECUTED
activation: NOT CLAIMED
```

This repair intentionally does **not** create a new provider broker, Vault, credential exchange, or execution authority. Future external-provider output must enter through an already-admitted TV/TVC provider-operation route and remain advisory/evidence-only under the bridge authority boundary.
