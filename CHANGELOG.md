# Changelog

## [1.0.0] — 2026-04-27 — Production Release

### Breaking Changes (from v0.1 human-in-the-loop)
- **Purpose**: General human-in-the-loop → Internal ecosystem adapter #2
- **human_gate default**: `true` → `false` (exception-only)
- **Session traces**: Markdown prose → Structured JSON with admission metadata
- **No CGE** → Embedded CGE Light per-org with BCAT/GCAT at every step
- **No receipts** → Hash-chained, verified receipts for all operations
- **No entity identity** → Every adapter tagged with governed entity (owner_human + owner_ai)

### Added
- CGE Light embedded governance engine (`cge_light/`)
- 10 provider adapters (Claude, OpenAI, Kimi, Gemini, Grok, DeepSeek, Perplexity, Ollama, Mock, Custom template)
- Provider discovery engine (`/v1/discover`) — auto-scan, query, connect
- BCAT/GCAT admission gate — every proposal, every output, every merge
- Receipt chaining for full traceability
- Entity identity registry with `Beta_Orionis` as owner AI
- Constitutional quorum rules (human+AI pair for policy changes)
- Emergency halt circuit breaker (`/v1/halt`)
- Governance dashboard (`/v1/dashboard/*`) — read-only ledger, receipts, entities, stats
- StegDB integration client (direct/filesystem/queue modes)
- FinCo compensation tracker (per-evaluation micro-payments)
- TV/TVC ephemeral secret management — zero hardcoded secrets
- Docker Compose with TVC sidecar on internal network
- Full test suite (CGE, governance, discovery)
- CI/CD workflow (validate, test, smoke, discovery, offline)

### Security
- All secrets via TV/TVC — no raw API keys in files, env, Docker, or git
- Auto-refresh credentials 5 min before expiry
- Explicit invalidation API
- Emergency halt requires quorum (any 2 of [human, AI, policy_engine])

### Infrastructure
- Platform-agnostic: works with HashiCorp Vault, AWS KMS, Azure Key Vault, custom TVC
- Offline-capable: Ollama local inference when network unavailable
- Graceful degradation: missing providers skipped, bridge continues
