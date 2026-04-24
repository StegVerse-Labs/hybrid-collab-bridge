# hybrid-collab-bridge

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

## Documentation

- [`docs/DISCOVERY_API.md`](docs/DISCOVERY_API.md) — Provider discovery, connection, and denial handling

## License

StegVerse Constitutional License — all changes require human+AI quorum.
