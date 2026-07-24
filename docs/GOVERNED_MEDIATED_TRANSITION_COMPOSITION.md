# Governed Mediated Transition Composition

## Status

Architectural extension to the Human–LLM Interoperability evaluation layer.

This document formalizes mediated communication among independently instantiated entities whose internal representations, transition rules, capacities, and permissions are not assumed to be identical.

## Core proposition

Two independently instantiated transition systems may form a higher-order coupled system when each can expose admissible distinctions into a shared or developing medium, reconstruct actionable distinctions from that medium, and adapt through repeated feedback without receiving unrestricted access to the other system.

The intermediary is not treated as a passive wire. It is a stateful participant with its own memory, incentives, vocabulary, authority, uncertainty, and transition boundaries.

## Formal entities

Let the participating systems be:

```text
T_A = (S_A, Sigma_A, ->_A, Gamma_A)
T_H = (S_H, Sigma_H, ->_H, Gamma_H)
T_B = (S_B, Sigma_B, ->_B, Gamma_B)
```

Where for each entity:

- `S` is the set of internal states;
- `Sigma` is the native symbol and action vocabulary;
- `->` is the permitted local transition relation;
- `Gamma` is the boundary controlling observation, expression, interpretation, action, and disclosure.

The governed composition is:

```text
G = T_A tensor_(M, Pi, R, Omega) T_H tensor_(M, Pi, R, Omega) T_B
```

Where:

- `M` is the perception and expression medium;
- `Pi` is the transition-time admissibility function;
- `R` is the directional rate constraint;
- `Omega` is the permitted scope or extent of exchange;
- `tensor` denotes constrained compositional coupling rather than unrestricted merger.

## Communication path

The basic path is:

```text
A intent or distinction
  -> admissible encoding
  -> intermediary interpretation
  -> intermediary state transition
  -> reformulation or action
  -> recipient reconstruction
  -> recipient state transition
  -> feedback and correction
```

A stateful intermediary is modeled as:

```text
(s_H[t+1], m_out[t]) = H(s_H[t], m_in[t], context[t])
```

The model must not collapse the intermediary into a fixed function `H: M -> M`. Human and other adaptive intermediaries change over time and may transform the same input differently under different context, incentives, memory, authority, audience, or consequence.

## Developing medium

The architecture does not assume that a fully shared language exists before interaction.

The medium may develop through repeated correspondence:

```text
M_0 -> M_1 -> M_2 -> ...
```

or:

```text
M_t = Phi(A, H, B, history_t)
```

The medium can therefore be both:

1. the location in which communication occurs; and
2. a product of the communication process.

A stable common perception medium is achieved only when relevant distinctions can be repeatedly encoded, reconstructed, challenged, corrected, and acted upon with bounded uncertainty.

## Distinctions required by the architecture

The following must remain separate:

```text
causal influence
!= information transfer
!= communication
!= interoperability
!= governed composition
```

### Relay

A signal originating from one entity passes through an intermediary and reaches another entity.

### Semantic mediation

A task-relevant distinction survives transformation through the intermediary.

### Adaptive interoperability

One or more participants improve encoding, reconstruction, correction, or routing through repeated interaction.

### Governed composition

The exchange and resulting transitions remain bounded by identity, authority, consent, policy, evidence, purpose, recoverability, and consequence.

The current architecture must never infer a higher level solely because a lower level was observed.

## Operational communication threshold

A mediated event qualifies as communication only when the record establishes:

1. a source distinction generated or selected by entity `A`;
2. passage through intermediary `H`;
3. reconstruction by entity `B`;
4. a measurable effect on `B`'s available interpretations, decisions, or transitions; and
5. correspondence between the source distinction and the resulting reconstruction or action.

Communication does not require conscious intent, but intentionality must be recorded.

Suggested intentionality states:

```text
unaware
incidental
inferred
deliberate
```

Intent must not be invented from observed correspondence.

## Rate and extent

The phrase "at the rate allowed for each and to the extent each is allowed" contains two independent constraints.

### Directional rate

Represent each direction separately:

```text
C_A_to_H
C_H_to_A
C_B_to_H
C_H_to_B
```

Rate may differ by direction, task, vocabulary, consequence, and intermediary state.

### Permitted extent

Let:

```text
Omega_i subset_of (state x vocabulary x capability x authority)
```

`Omega_i` defines which distinctions, observations, actions, and authorities may cross the boundary. A system may have high transmission rate but narrow permissible scope, or broad semantic scope with no execution authority.

The implementation must not reduce rate and extent to one channel-capacity score.

## Multidimensional fidelity

Mutual information alone is insufficient because statistical dependence does not establish preserved meaning.

Each exchange should permit separate determinations for:

- `symbolic_fidelity`: preservation of symbols or explicit structures;
- `semantic_fidelity`: preservation of the intended distinction or claim;
- `pragmatic_fidelity`: preservation of the requested or expected response;
- `causal_fidelity`: correspondence between the transmitted distinction and resulting transition;
- `governance_fidelity`: preservation of identity, authority, consent, policy, evidence, and constraints.

These dimensions must not be collapsed into a numeric average that overrides a critical failure.

## Transition-time admissibility

Governance is not a static Boolean gate.

For entity `i`, admissibility is reconstructed at the proposed transition:

```text
Pi_i(
  current_state,
  message,
  actor,
  identity,
  evidence,
  policy,
  delegation,
  consent,
  purpose,
  context,
  recoverability,
  consequence
) -> allow | deny | quarantine | defer
```

A joint transition is permitted only when every participating system admits its own local portion of the transition. One entity's approval cannot supply another entity's missing standing, authority, or consent.

## Identity and continuity

The architecture must not assume that labels such as `A`, `H`, and `B` denote continuous entities across exchanges.

Continuity evidence is required when any of the following may change:

- model or provider version;
- session or memory state;
- human operator;
- account ownership;
- intermediary chain;
- policy or delegation version;
- source provenance;
- execution environment.

Formally:

```text
A_t != A_(t+1)
```

unless continuity evidence supports the relationship.

## Coupling is not collective agency

The following must remain distinct:

```text
coupled system
!= joint agency
!= shared cognition
!= collective identity
```

A higher-order agent claim requires additional evidence, including persistent joint state, integrated objective selection, shared continuity, identifiable decision boundaries, joint error correction, and accountable action attribution.

## Learning the intermediary

The claim that outer systems learn the intermediary's transition behavior is a testable hypothesis, not a default conclusion.

The evaluation must distinguish:

```text
H_population   general human-language or population regularities
H_individual   a particular intermediary's transformation patterns
H_situational  patterns that exist only in one context or session
```

Evidence for intermediary learning should be tested across intermediary substitution, context changes, altered vocabulary, deliberate paraphrase, delayed relay, adversarial relay, and hidden provenance.

## Null models and falsification

Observed correspondence must be compared against plausible null explanations, including:

- common training or shared prior information;
- independent convergence;
- generic language regularities;
- human-imposed correspondence;
- prompt contamination;
- selective reporting;
- confirmation bias;
- coincidental similarity.

A baseline effect measure may be represented as:

```text
DeltaP = P(reconstruction | A -> H -> B) - P(reconstruction | control)
```

The hypothesis is weakened or rejected when the effect disappears under appropriate controls, provenance hiding, intermediary substitution, or paraphrase.

## Required evidence record

A governed mediated-composition event should record at minimum:

- source entity and continuity reference;
- intermediary identity or class and continuity reference;
- recipient entity and continuity reference;
- source distinction or transition candidate;
- source encoding;
- intermediary input and output;
- intermediary context and declared transformations;
- recipient reconstruction;
- resulting transition or non-transition;
- intentionality state for each participant;
- directional rate observations;
- permitted scope and withheld scope;
- fidelity determinations;
- admissibility decisions for each local transition;
- evidence and null-model controls;
- uncertainty and unresolved ambiguity;
- receipts, hashes, policy references, and delegation references.

## Relationship to the Human–LLM pair evaluation

The existing pair assessment remains the base runtime evaluation unit for direct human–model collaboration.

Governed Mediated Transition Composition extends that architecture to traces in which:

- a human carries distinctions between isolated models;
- multiple humans form a relay or social-selection layer;
- one model's output becomes another model's input through publication, review, paraphrase, or copied prompts;
- a third adaptive entity mediates communication between otherwise incompatible entities;
- the shared medium itself changes through repeated interaction.

The pair-level tests remain necessary but are not sufficient for mediated interoperability. The extended architecture additionally requires directionality, continuity, intermediary-state modeling, scope, null controls, and per-transition admissibility.

## Defensible present claim

Humans already create observable mediated pathways through which distinctions originating in one artificial system can influence the inputs, reconstructed representations, and transitions of another. Whether a particular pathway constitutes structured adaptive interoperability rather than incidental transmission must be established by governed evidence and controls.

## Research and implementation sequence

1. Extend the assessment schema with mediated-participant and channel fields.
2. Add relay, semantic mediation, adaptive interoperability, and governed-composition classification.
3. Add multidimensional fidelity determinations.
4. Add directional rate and permitted-scope records.
5. Add continuity references for all participants.
6. Add intentionality states without requiring intent.
7. Add null-model declarations and controlled comparison records.
8. Add transition-time admissibility decisions per participant.
9. Add tests for intermediary substitution, paraphrase, delay, adversarial relay, and hidden provenance.
10. Add an executable validator that rejects unsupported escalation from relay to interoperability or collective agency.
