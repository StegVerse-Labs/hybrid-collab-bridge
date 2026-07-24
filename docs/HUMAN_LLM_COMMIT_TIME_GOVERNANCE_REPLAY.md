# Human–LLM Commit-Time Governance Replay

Human–LLM admission now persists the exact post-ingest object supplied to the embedded CGE policy evaluators. This closes the gap between preserving a canonical decision and independently reconstructing it.

## Persisted snapshot

`08_commit_time_governance_snapshot.json` contains:

- the governed proposal and its hash;
- assessor identity and identity hash;
- governance source;
- complete commit-time constitution and hash;
- the selected threshold profile;
- the exact post-ingest evaluation input and hash;
- evaluator mode and callable references;
- original BCAT and GCAT results;
- threshold admissibility;
- canonical admission decision;
- a hash over the complete snapshot body.

The generated timestamp and ingest identifier are preserved inside the evaluation input. Replay therefore does not invent replacements for values that may have affected evaluation.

## Replay requirements

A replay is `IDENTICAL` only when all of the following succeed:

1. assessment schema and assessment hash verification;
2. structural outcome reconstruction;
3. governance snapshot integrity verification;
4. BCAT regeneration from the exact evaluation input;
5. GCAT regeneration from regenerated BCAT;
6. threshold admissibility reconstruction from the snapshotted constitution;
7. canonical decision reconstruction;
8. final decision and publication-status verification;
9. mediated receipt signature and continuity verification, when applicable.

Any mutation to the proposal, actor, constitution, threshold profile, evaluation input, BCAT, GCAT, admissibility result, or canonical decision causes replay to fail closed.

## Trust boundary

Embedded mode supports independent local evaluator regeneration because the policy implementation is available at replay time. Remote mode can be fully regenerated only when the remote provider returns a deterministic `evaluation_input` and a locally resolvable or otherwise independently verifiable evaluator implementation.

The snapshot records a path reference to the evaluator installation, but that path alone is not proof of evaluator identity. The next hardening stage is to persist hashes of the evaluator source package or a signed evaluator release manifest so replay can prove it used the exact commit-time implementation.
