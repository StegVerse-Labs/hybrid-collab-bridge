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
