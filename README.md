<!-- badges:start -->
[![Badges Keeper](https://github.com/StegVerse-Labs/hybrid-collab-bridge/actions/workflows/docs-badge-sync.yml/badge.svg)](https://github.com/StegVerse-Labs/hybrid-collab-bridge/actions/workflows/docs-badge-sync.yml)
<!-- badges:end -->

# hybrid-collab-bridge v1.0.0

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
│  │              STEGDB / FINCO INTEGRATION                  │  │
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
- `POST /v1/continue` — mark session reviewed and finalize (supports quorum approval)

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

## CGE Light (per-org drop-in)

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

### Quorum Rules (Constitutional)

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

### Docker Compose

```bash
# TVC runs as internal sidecar — no external ports
docker-compose up -d tvc hybrid-bridge

# TVC is on internal network only
# Bridge requests credentials via Docker DNS: http://tvc:8080/v1
```

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

25/25 OK · 0 no-dispatch · 0 broken — _2026-07-24 21:23 UTC_
<!-- /workflows:status -->
