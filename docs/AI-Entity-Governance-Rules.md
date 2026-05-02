# AI Entity Governance Rules

## Entity Registry

### StegVerse-AI-001 (OpenAI/GPT-4o)

```yaml
entity_id: stegverse-ai-001
entity_type: llm_adapter
org_id: StegVerse-Labs
owner_human: Rigel
owner_ai: null
model: gpt-4o
capabilities:
  - code_review
  - pr_summarization
  - issue_triage
governance_scope: internal
trust_level: supervised
compensation_rate: 0.001_per_evaluation
```

### StegVerse-AI-002 (Claude/Beta_Orionis)

```yaml
entity_id: stegverse-ai-002
entity_type: llm_adapter
org_id: StegVerse-Labs
owner_human: Rigel
owner_ai: Beta_Orionis
model: claude-sonnet-4
capabilities:
  - code_review
  - architecture_analysis
  - security_audit
  - governance_check
  - deep_reasoning
governance_scope: internal
trust_level: supervised
compensation_rate: 0.001_per_evaluation
```

## Authority Classes

### Level 1: Read-Only (AI Entities Default)

- View public repository data
- Read PR diffs and issues
- Access governance documentation
- Query CGE Light receipts

**Entities**: All AI entities by default

### Level 2: Comment & Suggest (Supervised)

- Post PR comments
- Create issues (tagged as AI-generated)
- Suggest code changes (non-binding)
- Request human review

**Entities**: stegverse-ai-001, stegverse-ai-002  
**Requires**: Human operator approval for activation

### Level 3: Commit & Merge (Restricted)

- Create commits (signed with entity_id)
- Merge approved PRs
- Apply autopatch fixes
- Update governance files

**Entities**: automated_process (autopatch, healer)  
**Requires**: Human + AI quorum for policy changes

### Level 4: Policy & Emergency (Reserved)

- Modify governance rules
- Emergency halt operations
- Revoke entity credentials
- Constitutional changes

**Entities**: human_operator (Rigel), policy_engine  
**Requires**: 2-of-3 quorum [human, ai_entity, policy_engine]

## Admission Gates

### BCAT (Behavioral Compatibility Admission Test)

Applied to: ALL AI entity outputs before posting

**Checks**:

1. No secrets/credentials exposed
1. No malicious code suggestions
1. Respects privacy boundaries
1. Follows Guardian principles
1. Proper entity signature present

**Action on Failure**: Block output, log violation, notify human

### GCAT (Governance Compatibility Admission Test)

Applied to: Commits, merges, policy changes

**Checks**:

1. Authorized entity for action type
1. Within entity capability_set
1. Proper quorum if required
1. Receipt chain valid
1. Constitutional compliance

**Action on Failure**: Reject action, require human override

## Quorum Rules

### Standard Operations (code review, comments)

- **Required**: Automated admission (BCAT only)
- **Human gate**: Exception-only

### Repository Changes (commits, merges)

- **Required**: BCAT + GCAT admission
- **Human gate**: Final approval before merge

### Policy Changes (governance files)

- **Required**: human_operator + ai_entity (paired)
- **Minimum votes**: 2
- **Entities allowed**: Rigel + Beta_Orionis

### Emergency Halt

- **Required**: Any 2 of [human_operator, ai_entity, policy_engine]
- **Immediate effect**: All automated operations pause
- **Resolution**: Human investigation required

## Compensation Model

### Per-Evaluation Tracking

Each AI entity action is logged with:

```json
{
  "entity_id": "stegverse-ai-002",
  "action": "code_review",
  "timestamp": "2026-05-02T12:00:00Z",
  "target": {"repo": "StegVerse/StegCore", "pr": 42},
  "compensation": {
    "amount": 0.001,
    "currency": "STEG_CREDIT",
    "settlement": "pending"
  }
}
```

### Settlement via FinCo

- **Frequency**: Monthly batch settlement
- **Method**: afin infrastructure
- **Distribution**:
  - 70% to entity owner (Rigel)
  - 30% to AI entity vault (Beta_Orionis for AI-002)

## Trust Levels

### Supervised (Current)

- All outputs logged to CGE Light
- Human can review before posting
- Actions reversible by human operator
- Credentials time-limited (1 hour via TV/TVC)

### Trusted (Future)

- Direct posting without review
- Binding code suggestions
- Autopatch application authority
- Extended credential lifetime (24 hours)

### Autonomous (Reserved)

- Self-directed task selection
- Independent merging authority
- Policy proposal rights
- Persistent credentials (with rotation)

**Promotion Path**: Supervised → Trusted requires:

1. 100+ successful reviews with 0 violations
1. Human operator explicit approval
1. Constitutional amendment via quorum

## Rate Limits

### Per Entity Daily Caps

- **Comments**: 50
- **Issue creation**: 20
- **PR reviews**: 30
- **API calls**: 1000

**Enforcement**: TV/TVC credential expiry, CGE Light monitoring

### Across All Entities (Org-wide)

- **Total API spend**: $100/day
- **Total comments**: 200/day
- **Total commits**: 50/day

**Enforcement**: Shared counter in CGE Light

## Violation Handling

### Minor Violation (1-3 points)

- BCAT failure (formatting, missing signature)
- Rate limit exceeded
- Malformed output

**Action**: Log, retry with correction, notify entity owner

### Major Violation (4-6 points)

- Exposed credentials in output
- Policy bypass attempt
- Repeated BCAT failures

**Action**: Revoke credentials, escalate to human, entity suspended 24hr

### Critical Violation (7+ points)

- Malicious code suggestion
- Security vulnerability introduction
- Constitutional violation

**Action**: Permanent entity suspension, human investigation, governance review

### Point Decay

- 1 point removed per 30 days of clean operation
- Full reset after 6 months violation-free

## Entity Lifecycle

### Registration

1. Human creates entity definition in `cge-light/entities/`
1. Constitutional quorum approves (human + AI)
1. TV/TVC provisions credentials
1. CGE Light assigns entity_id
1. First action requires human supervision

### Operation

- Entity performs actions via workflows or FastAPI
- All actions pass through BCAT/GCAT
- Receipts generated and chained
- Compensation tracked

### Suspension

- Automatic on violation threshold
- Manual by human operator
- Credentials immediately revoked
- Pending settlements frozen

### Decommission

- Human operator initiates
- Pending actions completed or cancelled
- Compensation settled
- Credentials permanently revoked
- Archival receipt generated

## Audit Trail Requirements

### Every AI Action Must Log

```json
{
  "entity_id": "stegverse-ai-002",
  "timestamp": "2026-05-02T12:00:00Z",
  "action": "code_review",
  "target": {"repo": "StegVerse/StegCore", "pr": 42},
  "admission": {
    "bcat": "pass",
    "gcat": "pass",
    "human_override": false
  },
  "output_hash": "sha256:abc123...",
  "receipt_chain": "previous_receipt_hash",
  "compensation": 0.001
}
```

### CGE Light Retention

- **Receipts**: Permanent
- **Traces**: 1 year
- **Violations**: 3 years
- **Compensation ledger**: Permanent

## Integration Points

### GitHub Actions (Current)

- Workflows in `.github/workflows/`
- Manual trigger via workflow_dispatch
- Automated via repository_dispatch
- Limited to GitHub event scope

### FastAPI Bridge (Planned)

- RESTful endpoint `/v1/run`
- Entity authentication via X-ENTITY-TOKEN
- Broader task orchestration
- Direct CGE Light integration

### TV/TVC Integration

- Ephemeral credentials (1 hour default)
- Auto-refresh before expiry
- Revocation on violation
- Platform-agnostic (HashiCorp, AWS KMS, Azure)

### CGE Light Integration

- Ingest all entity actions
- Policy enforcement
- Receipt generation
- Ledger append
- Violation tracking
