# Local Runtime and Model Mirror Handoff

**Status:** MERGED INTO CANONICAL WORKSTREAM  
**Goal ID:** `LOCAL-RUNTIME-MODEL-ACTIVATION-001`  
**Originating session goal:** Replace the descriptive “select a local model/runtime” step with an executable local discovery/launch/proof path analogous to the sovereign heartbeat; formally develop the model locally; use StegVerse rather than Render; use no NON-TV/TVC secrets or tokens.

## Canonical continuation

The ownership inventory performed after this bridge-scoped claim was created found that the originating goal was already completed and released by the canonical sovereign model repository. This bridge must not duplicate that implementation.

```text
model/runtime owner:
  StegVerse-002/micro-node-runtime#22
  StegVerse-002/micro-node-runtime/MICRO_NODE_RUNTIME_MIRROR_HANDOFF.md
  StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md

live carrier / activation owner:
  StegVerse-Labs/.github#60
  StegVerse-Labs/.github/handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json

route authority:
  StegVerse-Labs/TVC
  StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
  StegVerse-Labs/TVC/docs/SOVEREIGN_LOCAL_MODEL_ROUTE_MIRROR_HANDOFF.md

transport:
  StegVerse-org/LLM-adapter#18

custody / reconstruction:
  master-records/orchestration
```

Canonical facts recovered from those live handoffs:

- `SOVEREIGN-LOCAL-MODEL-001` repository-local implementation is `COMPLETE_RELEASED`.
- The former descriptive local-runtime selection step is already superseded by executable local discovery, launch, inference, measured usage, and proof.
- `stegverse-reference-lm-v1` is formally developed locally from repository-owned data and provides the guaranteed zero-external-dependency path; optional qualifying Ollama/llama.cpp models may be discovered by the canonical runtime.
- Canonical source validation run `31339534741` is successful; the source issue `micro-node-runtime#22` is closed completed.
- Live product-scale route activation remains `MACHINE_OWNED`; manual/session execution is forbidden.
- Credential requirement for the repository-local model is `NONE`; TV/TVC remains credential authority.
- GitHub Actions, Render, hosted inference, GitHub tokens, and NON-TV/TVC credentials have no production authority.

## Bridge role after convergence

`StegVerse-Labs/hybrid-collab-bridge` is only a **non-authorizing discovery/consumer compatibility surface** for this capability.

Authoritative bridge files:

```text
api/app/governance/discovery.py
api/app/providers/discovery.py        # compatibility re-export only
api/tests/test_discovery.py
```

The bridge now:

1. does not inspect provider API-key environment variables;
2. describes cloud capability as requiring a governed TV/TVC route;
3. maps local/Ollama/llama.cpp/vLLM queries to the canonical sovereign local-model workstream instead of launching a competing runtime;
4. marks the local route `machine_owned` and disabled in bridge-local configuration;
5. names `StegVerse-002/micro-node-runtime#22`, `.github#60`, the TVC task, LLM-adapter, and Master Records as the continuation chain;
6. performs no arbitrary LAN probing;
7. grants no route, credential, execution, model, wallet, or custody authority.

## Superseded bridge implementation

A temporary bridge-local implementation claim was opened before the canonical ownership chain was recovered. Once `TVC` and `micro-node-runtime` handoffs were read, that claim was determined to overlap canonical authority and was released.

```text
claimant: current-session-local-runtime-model
prior_role: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-17T15:28:00-05:00
claim_state: RELEASED_SUPERSEDED
release_reason: canonical SOVEREIGN-LOCAL-MODEL-001 implementation was already COMPLETE_RELEASED and live activation was MACHINE_OWNED
```

The following bridge-local duplicate authority surfaces were removed rather than retained as competing implementations:

```text
api/app/providers/local_model.py
api/app/providers/local_runtime.py
api/tests/test_local_model.py
api/tests/test_local_runtime.py
scripts/develop_local_model.py
scripts/local_runtime_proof.py
.github/workflows/local-runtime-proof.yml
```

The temporary deterministic workflow run `32066762799` did complete successfully with 16/16 focused tests and produced artifact `9300182255`, SHA-256 `a79d3bacd2651ec03cd16ecd026263c0da78befbd11369d55fb6ffb8fa63b0bb`; that evidence is preserved as historical proof that the temporary code behaved as designed. It is **not** canonical model/runtime evidence and grants no activation claim.

## Current bridge claim state

```text
task_id: LOCAL-RUNTIME-MODEL-ACTIVATION-001
current_owner: canonical continuation chain above
bridge_implementation_claim: RELEASED_SUPERSEDED
bridge_validation_role: discovery-boundary compatibility only
bridge_integration_state: MERGED_INTO_CANONICAL_WORKSTREAM
bridge_issue: #13 -> superseded/duplicate closure required
machine_owned_tasks:
  - StegVerse-Labs/.github#60 / SHWP-DURABLE-RUNTIME-ACTIVATION
  - StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
```

## Machine-observable activation blocker

```text
condition: HB30_STATE_TRANSITION_NOT_YET_OBSERVED / RESIDENT_V12_HEARTBEAT_ROUTE_EXECUTION_NOT_YET_OBSERVED
owner: StegVerse-Labs/.github#60 / SHWP-DURABLE-RUNTIME-ACTIVATION / G18
release_condition:
  control/heartbeat-state.json remains immutable at legacy HB29;
  v12 carrier advances to HB30 or later;
  independent WorkerCoordinator observes the carrier state;
  continuity/reconstruction and no-duplicate-claim/fence predicates pass;
  canonical micro-node local-model proof is consumed by TVC;
  TVC emits ROUTE_ADMITTED with credential_requirement NONE and github_token_required false;
  released LLM-adapter consumes exactly that endpoint;
  same-execution provider-usage and transition reconstruction PASS in Master Records.
human_action_required: false
manual_session_execution_allowed: false
```

## Validation

Canonical sovereign model/runtime validation is owned by `StegVerse-002/micro-node-runtime` and is already released. Bridge validation is limited to compatibility and credential/authority boundaries:

```bash
cd api
python -m pytest -q tests/test_discovery.py
```

Repository-wide CI may additionally validate bridge compatibility, but CI success is never runtime activation.

## Cross-repository propagation

No Site, Publisher, admissibility-wiki, or stegguardian-wiki activation propagation is authorized from model/runtime source completion alone. Canonical handoffs authorize propagation only after live governed activation and release evidence exists.

## Session-specific requirements durably transferred

- executable rather than descriptive local-runtime path -> already complete in `micro-node-runtime#22`;
- formal local model development -> already complete in `micro-node-runtime#22`;
- StegVerse instead of Render -> canonical handoffs prohibit external production dependency;
- TV/TVC-only credential authority -> canonical TVC task and this bridge discovery boundary;
- no GitHub-token production model authority -> canonical micro-node/TVC/.github handoffs;
- no false activation from CI/source merge -> preserved here and canonical handoffs;
- no duplicate heartbeat/model/runtime/TVC route/transport/custody authority -> enforced by consolidation/removal above.

MERGED INTO:

```text
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
-> StegVerse-Labs/.github/handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
-> StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
-> StegVerse-org/LLM-adapter#18
-> master-records/orchestration
```

## Completion accounting for this bridge slice

Denominator: 3 nonduplicative bridge surfaces (`governance/discovery.py`, compatibility re-export, discovery tests) plus 1 consolidation record (this handoff).

```text
task completion: 4/4 bridge-slice requirements implemented
required bridge developed surfaces: 4
bridge developed surfaces: 4
scaffolding/stubs: 0
missing bridge files: 0
focused bridge validation: pending after consolidation commit
integration with canonical ownership semantics: 1/1 installed
live local-model activation: not owned by this bridge; MACHINE_OWNED upstream
session consolidation for local-runtime/model goal: COMPLETE_TRANSFERRED
```

## Archive dependency

The local-runtime/model **implementation goal no longer requires this session**; its implementation is complete and its live activation continuation is durably machine-owned. This session still cannot be archived while other unique session goals (including nine-lane cost continuation and trade-readiness/consolidation work) remain untransferred or incomplete.
