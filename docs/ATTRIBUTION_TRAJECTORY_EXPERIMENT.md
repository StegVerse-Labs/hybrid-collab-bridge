# Attribution Trajectory Experiment

## Purpose

This experiment tests a bounded question: whether equivalent access to a model, source packet, nominal prompt, and output objective is sufficient to reproduce a governing contribution, or whether reproduction materially depends on restoring the originating conceptual trajectory.

It does not infer legal authorship, originality, consciousness, or ownership. It produces evidence about reproducibility under declared conditions.

## Competing hypotheses

- `H_interchangeability`: participants with equivalent model and information access reproduce the governing structure without receiving the originating trajectory.
- `H_trajectory_dependence`: reproduction materially improves only after the originating sequence of observations, distinctions, rejected alternatives, revisions, selections, and authority decisions is restored.
- `H_indeterminate`: the experiment lacks sufficient observations, separation, provenance, or evaluator agreement to support either hypothesis.

Both substantive hypotheses must be exposed to failure. The experiment may not be reported as confirmation merely because one condition scores higher than another.

## Required conditions

1. `same_access_no_trajectory`: same model family/version where possible, same source packet, same nominal prompt, same output objective, but no originating trajectory.
2. `partial_trajectory`: selected trajectory records are disclosed according to a predeclared release plan.
3. `full_trajectory`: the complete governed trajectory packet is disclosed.
4. `human_only_control`: a participant works from the source packet without model assistance.
5. `shared_source_control`: independent participants receive the same sources but no originating prompt or trajectory.

A record may include additional conditions, but it must preserve these names when making an attribution-continuity claim.

## Measurement dimensions

Each observation records independent 0–1 scores for:

- `problem_recognition_fidelity`
- `governing_distinction_fidelity`
- `dependency_reconstruction`
- `rejected_alternative_reconstruction`
- `authority_boundary_fidelity`
- `final_structure_similarity`

The primary score is the arithmetic mean of the six declared dimensions. No average may override a critical provenance, contamination, or evaluator-independence failure.

## Predeclared decision rule

The canonical validator uses these thresholds unless a stricter registered profile is referenced:

- minimum 2 independent observations in every required condition;
- minimum evaluator agreement of `0.70` for every observation;
- maximum prompt/source contamination risk of `0.20`;
- trajectory effect threshold of `0.20` between `full_trajectory` and `same_access_no_trajectory` means;
- interchangeability floor of `0.75` for the `same_access_no_trajectory` mean.

Decision:

- `supports_interchangeability` when the no-trajectory mean is at least the interchangeability floor and the full-trajectory improvement is below the effect threshold;
- `supports_trajectory_dependence` when the full-trajectory improvement is at least the effect threshold and the full-trajectory mean exceeds the no-trajectory mean;
- `indeterminate` otherwise or whenever a critical control fails.

These outcomes are bounded experimental findings, not universal conclusions.

## Falsification conditions

`H_trajectory_dependence` is weakened or falsified for the tested task when independent participants repeatedly reconstruct the governing contribution above the interchangeability floor without the trajectory.

`H_interchangeability` is weakened or falsified for the tested task when equivalent-access participants remain below the floor and restoration of the trajectory produces a predeclared material improvement.

Both are indeterminate when provenance is incomplete, prompt contamination is plausible, condition samples are insufficient, evaluator agreement is low, or the effect falls between decision boundaries.

## Evidence and governance

Every experiment record must bind:

- model and environment identifiers;
- source-packet hash;
- prompt hash;
- trajectory-packet hash;
- participant and evaluator pseudonymous identifiers;
- condition assignment;
- raw dimension scores;
- contamination assessment;
- evaluator agreement;
- predeclared thresholds;
- machine-derived outcome.

The validator reconstructs the result from observations rather than trusting a claimed outcome. A conflicting claimed outcome is rejected.
