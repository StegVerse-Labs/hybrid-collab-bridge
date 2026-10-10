<!-- badges:start -->
[![Badges Keeper](https://github.com/StegVerse-Labs/hybrid-collab-bridge/actions/workflows/docs-badge-sync.yml/badge.svg)](https://github.com/StegVerse-Labs/hybrid-collab-bridge/actions/workflows/docs-badge-sync.yml)
<!-- badges:end -->

# hybrid-collab-bridge v1.2

## Conformance status (HCB-VERSIONED-CONTRACT-038, issue #38)

Version: `v1.2` (single value from `VERSION`). Canonical handoff: [`HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md`](HYBRID_COLLAB_BRIDGE_MIRROR_HANDOFF.md).

HCB is optional and never a mandatory hop; all of its outputs carry `authority_effect: NONE`. Authority on the declared path belongs to Interlock/InTr, reached through SDK manifest submission. HCB awaits no external machine, receiver or observer. Every non-ALLOW state carries `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`.

| Surface | Classification | Meaning |
|---|---|---|
| `api/app/governance/admission.py` (BCAT/GCAT allow/deny/defer) | `LEGACY_ISOLATE` | Local evidence only, non-authorizing; never an admission decision on the declared path |
| `cge-light/` (embedded CGE ledger and receipts) | `LEGACY_ISOLATE` | Local trace evidence only, non-authorizing; not the org ledger |
| Quorum rules and `POST /v1/continue` | `LEGACY_ISOLATE` | Non-authorizing; a quorum approval confers no authority |
| `DEFERRED` / `requires_human` run parking | `LEGACY_ISOLATE` | Non-authorizing; nothing on the declared path waits on it |
| `render.yaml` (hosted Render service) and `Dockerfile.style-api` | `REMOVED` | Deleted; no reachable caller (only its own shape test and a CI `docker build` step, both removed) |
| `infra/docker-compose.yml` (tvc sidecar, ollama container, `HCB_STEGDB_ENDPOINT`, `depends_on`), `infra/Dockerfile`, `api/dockerfile` | `REMOVED` | Deleted; referenced only by docs |
| StegDB (`HCB_STEGDB_ENDPOINT`; `governance/stegdb.py`, `governance/stegdb_wiring.py`, `/v1/stegdb/*`) and publisher (`PUBLISHER_ENDPOINT`; `governance/publisher.py`, `/v1/publish/*`) | `REMOVED` | Optional external-service calls; references removed from `api/app/main.py` and modules deleted |
| `api/app/providers/{admission,cge_client,compensation,dashboard,halt,stegdb,entity,discovery}.py`, top-level `app/` | `REMOVED` | Diverged duplicates / unimportable copies; no importer |
| Remote CGE mode (`HCB_CGE_MODE=remote`, `HCB_CGE_ENDPOINT`; httpx POSTs to `/v1/ingest` and `/v1/ledger/append` in `governance/cge_client.py`) | `REMOVED` | External service and competing ledger; no workflow or test set it. Embedded is the only mode; any other `HCB_CGE_MODE` fails closed with six-field `REMOTE_CGE_REMOVED` and contacts nothing. `httpx` stays in `api/requirements.txt` for `providers/ollama_text.py` and `providers/custom_template.py` |
| `stegtvc_client.py` | `KEPT` | Local deterministic stub, no network; imported by `.github/ai_entity_runner.py` and the `diagnostic` / `stegtv-connectivity-diagnostic` workflows |
| `requirements-style-api.txt` | `KEPT` | Declared dependency surface of the FastAPI style API (`api/app/style_api.py`); asserted minimal by `tests/test_style_api_deployment.py` |

Sections below that describe these surfaces document legacy behavior, not current authority.

## Position in the StegVerse LLM Communications Stack

- **Stack ID:** `STEGVERSE-LLM-COMMS-STACK-v1`
- **Component ID:** `hybrid-collab-bridge`
- **Bounded role:** Internal multi-model collaboration adapter for governed expert coordination, synthesis, admission, trace creation, and collaboration receipts.
- **Consumes:** Governed collaboration requests, provider capabilities, policy and admission inputs, and evidence references.
- **Produces:** Expert traces, synthesis candidates, admission results, collaboration receipts, and governed return payloads.
- **Does not own:** General provider brokerage, model hosting, communication-source normalization, continuity truth, identity, commit-time execution authority, publication authority, or Master Records batch-receipt recording (a downstream, non-gating recorder of released organization batch receipts; see `docs/MASTER_RECORDS_ROLE.md`).

Canonical stack reference: [`docs/LLM_COMMUNICATIONS_STACK_POSITION.md`](docs/LLM_COMMUNICATIONS_STACK_POSITION.md)

For Ecosystem Chat external inference, the bridge consumes only retained provider-observation references. The provider-neutral execution primitive remains `StegVerse-org/LLM-adapter:llm_adapter/external_llm_connection.py`; using that primitive does not route an established Ecosystem Chat Node through the adapter's external-framework `/api/sdk/*` admission lane. The collaboration-side evidence contract is `schemas/ecosystem_chat_external_inference_session.schema.json`; provider output and any comparison/consensus remain `authority_effect=NONE`.

A **governed internal ecosystem adapter**: API orchestration + BCAT/GCAT admission + CGE-monitored traces.

- **Internal-only**: Second LLM adapter within the StegVerse ecosystem (user-facing SDK is adapter #1)
- **BCAT/GCAT admissibility**: Every proposal, every expert output, every merge is evaluated before execution
- **Minimal human gate**: Human review is exception-only, not default
- **CGE-monitored**: Every operation is ingested into org-local CGE Light with hash-chained receipts
- **Entity-governed**: Every adapter instance is tagged with a governed AI entity identity (owner: you + Beta_Orionis)
- **Compensation-ready**: Per-evaluation tracking for FinCo/afin integration

## Architecture

```
PROPOSE -> ADMIT (BCAT/GCAT) -> EXECUTE -> PROVE -> RECEIPT
  ^                                              |
  +-- Human+AI quorum for policy changes <---------+
```


## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / CLIENT                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────────┐
│              FASTAPI BRIDGE (Port 8080)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ /v1/run     │  │ /v1/discover │  │ /v1/halt         │  │
│  │ /v1/continue│  │ /v1/connect  │  │ /v1/dashboard/*  │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                │                    │            │
│  ┌──────▼────────────────▼────────────────────▼─────────┐  │
│  │              GOVERNANCE LAYER                          │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ │  │
│  │  │Admission│ │ Discovery│ │ Emergency│ │Dashboard │ │  │
│  │  │  Gate   │ │  Engine  │ │  Halt    │ │ (read)   │ │  │
│  │  └────┬────┘ └────┬─────┘ └────┬────┘ └────┬─────┘ │  │
│  │       │           │            │            │       │  │
│  │  ┌────▼───────────▼────────────▼────────────▼─────┐ │  │
│  │  │              CGE LIGHT (embedded)                 │ │  │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │ │  │
│  │  │  │ Ingest │ │ Policy │ │ Ledger │ │ Receipts │  │ │  │
│  │  │  └────────┘ └────────┘ └────────┘ └──────────┘  │ │  │
│  │  └───────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│         │                           │                        │
│  ┌──────▼───────────────────────────▼────────────────────┐  │
│  │              TV/TVC SECRET MANAGEMENT                    │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────┐  │  │
│  │  │  TVC Client  │───→│ TV Vault    │───→│ Ephemeral│  │  │
│  │  │  (direct)   │    │ (HashiCorp  │    │ Token    │  │  │
│  │  │  (file)     │    │  AWS KMS    │    │ (1h TTL) │  │  │
│  │  │  (env)      │    │  Azure)     │    │          │  │  │
│  │  └─────────────┘    └─────────────┘    └──────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│         │                           │                        │
│  ┌──────▼───────────────────────────▼────────────────────┐  │
│  │              PROVIDER ADAPTERS (10 total)                │  │
│  │  Cloud: Claude, OpenAI, Kimi, Gemini, Grok,            │  │
│  │         DeepSeek, Perplexity                            │  │
│  │  Local: Ollama (no network, no secrets)                  │  │
│  │  Test:  Mock (always available)                         │  │
│  └────────────────────────────────────────────────────────┘  │
│         │                                                    │
│  ┌──────▼────────────────────────────────────────────────┐  │
│  │      FINCO INTEGRATION (StegDB ingestion REMOVED)        │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────┐   │  │
│  │  │ Receipt     │    │ Session     │    │Compensation│  │  │
│  │  │ Ingestion   │    │ Trace       │    │ Tracking  │  │  │
│  │  └─────────────┘    └─────────────┘    └──────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Quick start

```bash
# 1) env
cd hybrid-collab-bridge
cp .env.example .env
# Fill: ANTHROPIC_API_KEY, ADMIN_TOKEN

# 2) run API
cd api
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Endpoints

- `GET  /health` — returns bridge entity, CGE mode, providers
- `POST /v1/run` — start a governed collaboration (writes session folder with JSON traces)
- `POST /v1/continue` — mark session reviewed and finalize (supports quorum approval). `LEGACY_ISOLATE`, non-authorizing.

**Example**

```bash
export ADMIN_TOKEN=your_token
curl -s -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -H "X-ADMIN-TOKEN: $ADMIN_TOKEN" \
  -d '{
    "slug": "first-governed-run",
    "question": "Draft a 2-sentence pitch for StegTalk and list 3 next steps.",
    "context": "Audience: developers; emphasize privacy and onboarding.",
    "experts": ["claude"],
    "strategy": "consensus",
    "human_gate": false,
    "temperature": 0.3
  }' | jq .
```

Outputs go to `hybrid-collab-bridge/sessions/<today>/first-governed-run/`:

- `context.md`
- `01_claude.json` (structured trace with admission metadata + receipt)
- `03_referee.json` (merge trace with final admission + receipt chain)

## CGE Light (per-org drop-in) — `LEGACY_ISOLATE`, non-authorizing

The `cge_light/` directory contains a self-contained governance engine:

- `repo_contract.txt` — org identity, policy profile, entity model
- `repo_constitution.txt` — authority classes, mutation classes, quorum rules, thresholds
- `cge/` — ingest, ledger, policy, receipts, hashing, config

No external dependencies. No single point of failure. Every org bootstraps its own.

## Add more experts later

1. Create a provider in `api/app/providers/your_adapter.py`
2. Register it in `api/app/registry.py`
3. Add an entry in `providers.txt`

Adapters declare capabilities like `text-generate`, `image-generate`, `music-generate`.

## Governance Model

### Quorum Rules (Constitutional) — `LEGACY_ISOLATE`, non-authorizing

| Action | Required Approvers |
|--------|-------------------|
| Policy change | human_operator + ai_entity (paired) |
| Standard admission | automated_process |
| Emergency halt | any 2 of [human_operator, ai_entity, policy_engine] |

### Entity Identity

Every operation is tagged with:
- `entity_id` — unique identifier
- `entity_type` — llm_adapter, consensus_engine, automated_process
- `org_id` — StegVerse-Labs
- `owner_human` — you
- `owner_ai` — Beta_Orionis
- `capability_set` — authorized capabilities
- `governance_scope` — internal

### Compensation

AI entities receive per-evaluation micro-payments tracked in the ledger as `compensation` mutation class. Settled via FinCo/afin infrastructure.

## Ecosystem Context

| Org | CGE Type | Function |
|-----|----------|----------|
| StegGhost | Full Compiler CGE | Master governance, backup, oversight |
| GCAT-BCAT-Engine | CGE Light (Gemstone_IV) | Repo bootstrap, BCAT/GCAT baseline |
| StegVerse-org | Distributed per-repo | SDK, GSL, Demo Suite |
| AaCT-E | Distributed per-repo | TV, TVC, StegBrain, StegCore, Orchestration |
| **StegVerse-Labs** | **CGE Light (this repo)** | **Internal LLM adapter #2** |


## TV/TVC Secret Management

All API keys and tokens are managed through **TrustVault (TV)** + **TrustVaultController (TVC)**.

### Principles

- **No hardcoded secrets** — Only TVC reference IDs in config
- **Ephemeral credentials** — Auto-rotated, short-lived (default 1 hour)
- **Platform-agnostic** — Works with HashiCorp Vault, AWS KMS, Azure Key Vault, or custom TVC
- **Zero secrets in files** — `.env` contains only reference IDs, never raw keys
- **Auto-refresh** — Credentials refreshed before expiry (5-min buffer)

### Configuration

```bash
# .env — Only reference IDs, never raw keys
TVC_ENDPOINT=https://tvc.stegverse.org/v1
CRED_OPENAI=cred-openai-prod
CRED_ANTHROPIC=cred-anthropic-prod
```

### Docker Compose — `REMOVED`

`infra/docker-compose.yml` (tvc sidecar, ollama container) was deleted under HCB-VERSIONED-CONTRACT-038; HCB requires no container or sidecar.

### Development (File Mode)

```bash
# Copy example vault
cp .tv/vault.json.example .tv/vault.json
# Edit with your dev keys (never commit)

# Set mode
TVC_MODE=file
TV_VAULT_PATH=./.tv/vault.json
```

### Production (Direct Mode)

```bash
# TVC endpoint with auto-rotation
TVC_MODE=direct
TVC_ENDPOINT=https://tvc.stegverse.org/v1
TVC_API_KEY=tvc-prod-reference

# Credentials are fetched ephemeral, never stored locally
```

### Provider Adapter with TV/TVC

```python
from app.governance.tv_tvc import TVCClient, TVProviderAdapter
from app.providers.openai_text import OpenAIText

# Create TVC client
tvc = TVCClient(mode="direct")

# Wrap any provider with ephemeral credentials
base = OpenAIText("openai")
provider = TVProviderAdapter(base, tvc, "cred-openai-prod")

# Token is fetched ephemeral, used, discarded
result = await provider.run(task)
```

## Documentation

- [`docs/DISCOVERY_API.md`](docs/DISCOVERY_API.md) — Provider discovery, connection, and denial handling


## File Extensions Note

This repo uses `.txt` for all configuration files to ensure compatibility with iOS/Working Copy workflows where `.yml` files may have transfer issues.

**Exception**: GitHub-native files (`.github/workflows/*.yml`, `.github/autopatch/*.yml`) use `.yml` as required by GitHub Actions. These are not edited on iOS.

## License

StegVerse Constitutional License — all changes require human+AI quorum.

## Workflows Status

<!-- workflows:status -->
[![workflows](.github/badges/workflows.svg)](.github/docs/WORKFLOWS_STATUS.md)

27/27 OK · 0 no-dispatch · 0 broken — _2026-10-10 00:46 UTC_
<!-- /workflows:status -->

### Capability-addressed external AI contract

Ecosystem Chat capability discovery is provider-neutral. A capability descriptor may identify text, reasoning, code, image, video, audio, science, research, data, or a future `other` work class; its input/output media, provider/model, entitlement state, routing disposition, execution constraints, and required retained-observation return are descriptive metadata only and have `authority_effect=NONE`.

Provider availability and user entitlement are separate. A known provider may be discoverable while entitlement remains `UNKNOWN`; execution must not silently treat that as available. A resolved non-entitled paid capability uses `UPGRADE_REQUIRED` or `PURCHASE_REQUIRED`, while provider unavailability remains `PROVIDER_UNAVAILABLE`. No disposition silently substitutes another capability route.

The existing LLM-adapter `external_llm_connection` remains the governed execution primitive for the text/reasoning capability family. This bridge does not become a general provider broker, credential authority, SDK ingress, persistent runtime, or Node-identity owner. Specialized external AI surfaces remain disposable execution surfaces and their outputs remain independently retained, non-authoritative observations.
