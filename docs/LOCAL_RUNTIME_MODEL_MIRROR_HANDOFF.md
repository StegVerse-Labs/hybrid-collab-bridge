# Local Runtime and Model Mirror Handoff

**Status:** ACTIVE — UNIQUE IMPLEMENTATION CLAIM  
**Goal ID:** `LOCAL-RUNTIME-MODEL-ACTIVATION-001`  
**Originating session goal:** Replace the descriptive “select a local model/runtime” step with an actual local-runtime discovery, launch, and proof path analogous to the sovereign heartbeat; formally develop the local model path; use StegVerse rather than Render; keep all non-TV/TVC secrets and tokens out of this capability.

## Canonical owner and branch

- Organization: `StegVerse-Labs`
- Repository: `hybrid-collab-bridge`
- Branch: `main`
- Canonical handoff: `docs/LOCAL_RUNTIME_MODEL_MIRROR_HANDOFF.md`
- Existing provider-discovery surface: `api/app/providers/discovery.py`
- Existing Ollama adapter: `api/app/providers/ollama_text.py`
- Existing discovery tests: `api/tests/test_discovery.py`

This handoff is scoped to local model/runtime discovery, launch orchestration, runtime proof, model selection policy, and durable evidence. It does **not** supersede `HIL_MIRROR_HANDOFF.md` or claim HIL qualified-recognition activation work.

## Governing boundaries

1. Do not use Render for this capability.
2. Local runtimes must not require provider secrets or tokens.
3. Any cloud/provider credential authority remains outside this path and must be governed by TV/TVC.
4. GitHub Actions may validate code but is not runtime/control-plane authority.
5. Local runtime discovery or availability does not grant StegGate execution authority.
6. The runtime path must fail closed when proof is absent or inconsistent.
7. HIL machine-owned paths are collision boundaries and are not modified by this claim.

## Active implementation claim

```text
task_id: LOCAL-RUNTIME-MODEL-ACTIVATION-001
claimant: current-session-local-runtime-model
role: CLAIMED_FOR_IMPLEMENTATION
claimed_at: 2026-08-17T15:28:00-05:00
claim_scope:
  - docs/LOCAL_RUNTIME_MODEL_MIRROR_HANDOFF.md
  - api/app/providers/local_runtime.py
  - api/tests/test_local_runtime.py
  - scripts/local_runtime_proof.py
  - .github/workflows/local-runtime-proof.yml
collision_boundaries:
  - HIL_MIRROR_HANDOFF.md and HIL issue #11 machine-owned implementation
  - StegCore canonical admissibility evaluator
release_condition:
  - implementation files committed
  - deterministic tests/workflow installed
  - hosted validation evidence inspected when available
  - handoff updated with evidence and unresolved physical-host activation boundary
```

## Current state at claim creation

The repository already has descriptive/local probing logic in `api/app/providers/discovery.py` and an Ollama adapter. The existing discovery code can detect local servers, but it does not provide a canonical launch plan, bounded launch execution, normalized runtime/model inventory, proof receipt, proof validator, or durable local-runtime activation contract. The descriptive Ollama instructions therefore remain insufficient for the session goal.

## Required deliverables

1. `api/app/providers/local_runtime.py` — canonical runtime definitions, safe discovery, model inventory, bounded launch plan/execution, readiness probing, deterministic proof receipt creation and validation.
2. `api/tests/test_local_runtime.py` — deterministic tests using injected/mock command and HTTP surfaces; no real provider secrets.
3. `scripts/local_runtime_proof.py` — operator/machine entry point that emits a JSON proof receipt and returns nonzero when proof cannot be established.
4. `.github/workflows/local-runtime-proof.yml` — credential-clean static/deterministic validation lane; must not masquerade as physical-host activation.
5. Update `api/app/providers/discovery.py` to consume the canonical local-runtime discovery layer rather than maintaining a competing local runtime description.
6. Durable proof receipt only when a real local host executes the proof entry point successfully.
7. Formal local-model profile contract identifying selected runtime, selected model, model digest/identity when exposed by the runtime, endpoint, capabilities, and proof hash without credential material.

## Validation plan

```bash
python -m pytest api/tests/test_local_runtime.py -q
python scripts/local_runtime_proof.py --dry-run
python -m pytest api/tests/test_discovery.py -q
```

Hosted validation may prove deterministic implementation behavior only. A physical-host activation receipt requires a host that actually exposes or can launch a supported local runtime.

## Cross-repository dependencies and propagation

- `StegVerse-Labs/StegCore`: canonical admissibility remains authoritative; local runtime identity must not create a parallel evaluator.
- `StegVerse-Labs/.github`: sovereign heartbeat/carrier ownership remains separate; future physical-host runtime supervision may integrate there after this local runtime contract is validated.
- `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `StegVerse-Labs/admissibility-wiki`, `StegVerse-002/stegguardian-wiki`: propagation only after an activated and versioned local-runtime contract exists and each destination handoff is read.

## Session consolidation inventory

Transferred into this handoff:
- local-runtime discovery/launch/proof goal;
- formal local-model development requirement;
- StegVerse-not-Render constraint;
- TV/TVC-only credential authority constraint;
- no false activation from source or CI;
- collision prevention with machine-owned HIL and canonical StegCore authority;
- requirement for durable receipts and explicit physical-host activation boundary.

Adjacent trade-readiness and nine-lane cost work remain separate canonical workstreams and must not be silently counted as complete here.

## Completion accounting at claim creation

Denominator: 7 required deliverables above.

- Task completion: 1/7 (handoff/claim established).
- Developed files: 1/5 implementation/control files present in final form for this workstream (handoff only); the four executable/test/workflow files are missing.
- Scaffolding/stubs: existing descriptive discovery logic is treated as partial legacy implementation, not completion.
- Validation: 0/4 required validation levels complete for this new workstream.
- Integration: 0/2 (existing discovery integration; future sovereign host supervision integration).
- Goal activation: 0% until real local-host proof exists.
- Session consolidation: local-runtime/model requirements transferred; adjacent goals remain active elsewhere.

## Archive condition

This session is not archive-ready while this implementation claim is active or while unique local-runtime/model requirements have not been implemented, validated, or transferred to a durable machine-owned continuation path.
