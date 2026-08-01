# HIL Qualified Recognition and Participant Continuation Layer

**Capability ID:** `HIL-QRL-001`  
**Status:** implementation candidate — not activated

## Purpose

The layer preserves the difference between being acknowledged and being materially recognized. It records when a human contribution is accurately reconstructed, evaluated in the relevant domain, shown to affect subsequent work, attributed to its contributor, and used to propose an updated participation posture.

A qualified-recognition event is not praise, endorsement, identity verification, employment evaluation, authorship transfer, or final admissibility. It is a bounded evidence object requesting governed recognition of a contribution and its causal continuation.

## Core distinctions

- expression is not examination;
- acknowledgment is not incorporation;
- incorporation is not attribution;
- attribution is not standing;
- standing is not execution authority;
- visibility is not representativeness;
- classification membership is not authority to speak for the classified group;
- observed engagement is not consent to publication;
- candidate recognition is not admitted recognition.

## Formal object

Let:

- `p` be a participant;
- `c` be a contribution;
- `r` be a resulting artifact or state;
- `X(c)` be evidence that the contribution was reconstructed accurately;
- `D(c)` be evidence of domain-qualified examination;
- `T(c,r)` be a bounded causal-effect claim;
- `A(p,c)` be preserved attribution;
- `C(p,c,r)` be the applicable consent posture;
- `S0(p)` be prior participation standing;
- `S1(p)` be proposed subsequent standing;
- `R(c -> r)` be reconstructability of the contribution's effect.

A candidate qualified-recognition event may be emitted only when:

```
QRE_candidate = X(c) AND D(c) AND A(p,c) AND C(p,c,r) AND R(c -> r)
```

A material participant-continuation proposal additionally requires bounded causal evidence:

```
PC_candidate = QRE_candidate AND T(c,r) > 0 AND S1(p) >= S0(p)
```

Neither expression authorizes final admission. The final state is external:

```
QRE_admitted = PC_candidate AND admission_decision == ALLOW
```

## Required evidence fields

Every candidate receipt must contain:

1. stable receipt and trace identifiers;
2. contributor reference with explicit verification posture;
3. contribution reference and immutable digest where available;
4. reconstruction statement and supporting evidence references;
5. examiner qualification basis without overstating credentials;
6. causal-effect statement bounded to a named result;
7. attribution and consent posture;
8. prior and proposed standing classes;
9. scope and authority exclusions;
10. replay inputs;
11. admission state;
12. custody destination.

## Standing classes

This layer uses bounded participation classes rather than social rank:

- `observer` — may inspect public or authorized material;
- `contributor_candidate` — has supplied a traceable contribution not yet admitted;
- `recognized_contributor` — contribution admitted as materially affecting a bounded result;
- `continuing_participant` — may continue within the admitted scope;
- `reviewer_candidate` — may be considered for review work but has no review authority until separately admitted.

Recognition must never silently grant mutation, execution, publication, identity, financial, or governance authority.

## Scope-invalid authority projection

A speaker's statement is evidence that the statement occurred. It is not evidence that the speaker represents every member of a shared classification.

For speaker `s`, claim `C`, alleged group `G`, and time `t`:

```
observed(s, C, t) != authorized_to_represent(s, G, C, t)
```

Absent explicit evidence of representative authority, admissible claim scope remains bounded to the speaker and the observed statement.

## Runtime sequence

```
OBSERVE
  -> RECONSTRUCT CONTRIBUTION
  -> EXAMINE WITH DECLARED QUALIFICATION BASIS
  -> RECORD ATTRIBUTION + CONSENT POSTURE
  -> BOUND CAUSAL EFFECT
  -> PROPOSE STANDING TRANSITION
  -> VALIDATE SCHEMA + POLICY
  -> REQUEST BCAT/GCAT/CGE ADMISSION
  -> EMIT ADMITTED OR DENIED RECEIPT
  -> PRESERVE CUSTODY
```

## Fail-closed rules

The candidate must be denied or remain pending when:

- contributor identity or attribution is asserted beyond available evidence;
- consent posture is missing;
- the causal-effect claim cannot be reconstructed;
- the examination basis is absent or deceptive;
- group-level representation is inferred from individual expression;
- proposed standing exceeds the bounded contribution scope;
- publication or execution authority is implied;
- required evidence references are mutable or unavailable without disclosure;
- admission or custody evidence is absent.

## Activation gate

`HIL-QRL-001` remains inactive until deterministic validation, negative fixtures, admission integration, custody preservation, and replay evidence are committed and accepted under `HIL_MIRROR_HANDOFF.md`.
