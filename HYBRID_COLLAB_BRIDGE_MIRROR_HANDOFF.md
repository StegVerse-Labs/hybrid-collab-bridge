# Hybrid Collab Bridge Mirror Handoff

Repository: `StegVerse-Labs/hybrid-collab-bridge`
Current goal: HPS route bridge for sibling input nests
Status: initial HPS bridge package installing
Created: 2026-07-08

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-Labs/hybrid-collab-bridge`.

## Role correction

`StegVerse-org/StegVerse-SDK` and `StegVerse-org/LLM-adapter` should be sibling input nests.

The LLM adapter should not consume the SDK route decision as if SDK were upstream authority.

Instead:

```text
SDK input          \
                   -> hybrid-collab-bridge -> HPS route state -> next governed boundary
LLM-adapter input  /
```

## Ownership boundary

```text
Admissible-Existence/HPS
  -> mathematics, formalism, standing equation, HPS schemas/verifiers

master-records/orchestration
  -> ecosystem-wide orchestration, receipts, participant records, cycle state

StegVerse-Labs/hybrid-collab-bridge
  -> shared HPS route bridge for parallel input nests

StegVerse-org/StegVerse-SDK
  -> SDK-origin input nest

StegVerse-org/LLM-adapter
  -> LLM-origin input nest

StegVerse-Labs/Site
  -> visualization and user-facing preview surface
```

## Active goal

Install a shared HPS bridge contract that normalizes SDK-origin and LLM-origin route requests into a common HPS route state without granting execution authority.

## Required files

```text
docs/HPS_ROUTE_BRIDGE.md
schemas/hps.bridge.route.schema.json
examples/sdk_origin_hps_bridge_route.json
examples/llm_origin_hps_bridge_route.json
examples/expired_hps_bridge_route.json
scripts/verify_hps_bridge_route.py
tests/test_hps_bridge_route.py
receipts/hps_bridge_activation_receipt.json
```

## Non-authority rule

```text
The bridge does not execute.
The bridge does not publish.
The bridge does not grant authority.
The bridge normalizes route state for the next governed boundary.
```

## Archive posture

This handoff makes the HPS route bridge state recoverable. Future sessions should read this file before continuing hybrid bridge work.
