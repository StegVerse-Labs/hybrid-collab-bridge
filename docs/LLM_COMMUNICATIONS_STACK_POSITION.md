# Position in the StegVerse LLM Communications Stack

Stack identifier: `STEGVERSE-LLM-COMMS-STACK-v1`

`hybrid-collab-bridge` is the internal multi-model collaboration adapter within the distributed StegVerse LLM Communications Stack.

## This repository owns

- governed expert and provider coordination;
- collaboration-session construction;
- BCAT/GCAT admission of proposals, expert outputs, and merged results;
- synthesis and referee traces;
- collaboration-specific receipts;
- emergency halt and collaboration-governance surfaces;
- compensation-ready per-evaluation records.

## This repository consumes

- provider contracts and normalized LLM interactions from the common governed LLM broker;
- provider capabilities and credentials through governed provider and TV/TVC interfaces;
- policy and admission rules from BCAT/GCAT and associated governance components.

## This repository produces

- governed collaboration sessions;
- admitted, denied, or deferred expert outputs;
- synthesized result candidates;
- hash-chained collaboration traces and receipts;
- transition candidates for continuity, decision, communication, custody, or return paths.

## This repository does not own

- the common provider-neutral LLM broker contract;
- local model weights or inference custody;
- general communication-source normalization;
- continuity truth or identity;
- final commit-time authority;
- Master Record custody;
- external execution authority.

## Related stack components

- `StegVerse-org/LLM-adapter` — common governed LLM broker and reference adapter;
- `StegVerse-Labs/governed-llm` — StegVerse-controlled local inference provider;
- `StegVerse-Labs/Comms-Gateway` — communication-event normalization and routing;
- `StegVerse-Labs/StegCore` — commit-time decision engine;
- `GCAT-BCAT-Engine/workflows` — deterministic validation and cross-repository orchestration.

StegVerse-org and StegGhost deployments remain isolated Demo, conformance, adversarial, and entity-specific verification surfaces unless separate evidence establishes another deployment posture.


## Ecosystem Chat external-inference composition

For `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`, this repository owns only the collaboration-side composition of already-retained external inference evidence.

The canonical composition is:

```text
Site registered Node / Receipt #1
-> ephemeral Ecosystem Chat inference session
-> StegVerse-org/LLM-adapter provider-neutral external_llm_connection primitive
-> independently retained provider-response observations
-> this repository's retained-observation reference boundary
-> existing comparison / synthesis owner
```

The LLM-adapter provider-neutral primitive is reusable without traversing its external-framework `/api/sdk/*` admission surface. Provider-operation Interlock/InTr and TV/TVC boundaries remain the existing provider execution/admission machinery and are not SDK-lane Node admission.

This repository does not copy provider response bodies into a new broker contract. The session contract retains provider/model identity when observable, request correlation, exact response SHA-256, observation state, and `authority_effect=NONE`. Comparison or synthesis MUST cite retained observation IDs and MUST fail closed when a cited observation is absent or is not `RETAINED`. Disagreement remains represented by the independently retained observations. Consensus or synthesis does not grant execution, admission, governance, publication, continuity, or custody authority.

Canonical machine-readable contract: `schemas/ecosystem_chat_external_inference_session.schema.json`.
