# HPS Route Bridge

## Purpose

The HPS Route Bridge lets sibling input nests consume the same Harmonic Principle of Standing route state without making one input path subordinate to another.

This corrects the architecture from:

```text
LLM-adapter -> SDK -> HPS route decision
```

to:

```text
SDK input          \
                   -> HPS Route Bridge -> next governed boundary
LLM-adapter input  /
```

## Canonical sources

```text
Admissible-Existence/HPS
  -> canonical HPS formalism, standing equation, heartbeat/capability/expiration/verifier logic

master-records/orchestration
  -> ecosystem cycle state, receipts, participant records, reconstruction references
```

## Bridge responsibility

The bridge receives an input-origin route request and normalizes it into a shared HPS route decision surface.

Supported origins:

```text
SDK
LLM_ADAPTER
SITE
EXTERNAL_ADAPTER
MANUAL_REVIEW
```

The bridge may classify a route as:

```text
ALLOW_NEXT_BOUNDARY
DENY
REVIEW
FAIL_CLOSED
```

## Non-authority rule

```text
The bridge does not execute.
The bridge does not publish.
The bridge does not grant authority.
The bridge does not replace HPS formalism.
The bridge does not replace master-record orchestration.
```

`ALLOW_NEXT_BOUNDARY` means only that the request may continue to the next governed boundary.

## Route supports

A bridge route may proceed only when:

```text
heartbeat_result == PASS
standing_class satisfies standing_required
capability_window_state == OPEN
authority_valid == true
policy_current == true
delegation_current == true
evidence_fresh == true
coordinate_valid == true
reconstruction_available == true
expiration_triggers == []
```

## Sibling input rule

SDK-origin and LLM-origin inputs must be evaluated through the same bridge route contract.

```text
SDK-origin request and LLM-origin request are peer route candidates.
Neither one grants authority to the other.
```

## Failure posture

The bridge fails closed when it cannot establish current standing or reconstruction support.

```text
UNKNOWN heartbeat -> FAIL_CLOSED
FAILED standing -> FAIL_CLOSED
missing reconstruction -> FAIL_CLOSED
invalid coordinate -> FAIL_CLOSED
invalid authority for authority-bound route -> FAIL_CLOSED
expired capability window -> DENY
review-bound route -> REVIEW
```

## Canonical bridge statement

```text
The HPS Route Bridge is a sibling-input normalizer.
It accepts SDK-origin, LLM-origin, Site-origin, and external-adapter route candidates and maps them to a common HPS route state without granting execution authority.
```
