# Validation Only Adaptive Policy Selection

## Purpose and boundary

The first frozen selector was deliberately conservative and changed only one of
32 held-out replay decisions. Before any prospective human game, a separate
chronological validation corpus was therefore used to select the probability
conversion policy. No game outcome or final-test position was used for this
selection.

The experiment sampled 256 positions immediately before a historical opponent
of Yash moved. After excluding positions with fewer than eight legal root
candidates, 231 positions and 1,848 candidate rows remained. Every position was
searched once at 20,000 nodes and the resulting candidate corpus was reused for
all configurations.

## Grid and selection rule

- Probability scales: 50, 100, 200, and 400 cp per probability unit.
- Maximum model bonuses: 10, 20, and 35 cp.
- Candidate counts: MultiPV 4 and MultiPV 8.
- Objective eligibility loss bound: 35 cp in every configuration.
- Intended intervention range: 10% to 25% of validation positions.
- Selection rule: maximize mean personal-model probability lift inside that
  range; if no configuration enters the range, choose the configuration closest
  to its 17.5% midpoint, then prefer lower search loss and complexity.

No configuration quite reached 10%. The closest was selected by the written
fallback rule:

| Frozen setting | Value |
|---|---:|
| Probability scale | 400 cp per probability unit |
| Maximum bonus | 35 cp |
| MultiPV candidates | 8 |
| Validation changes | 23 / 231 (9.96%) |
| Mean search-score loss over all positions | 0.68 cp |
| Maximum search-score loss | 33 cp |
| Mean probability lift when changed | 5.01 percentage points |

The original 100 cp scale changed 6 of 231 positions (2.60%) regardless of
whether its cap was 10, 20, or 35 cp and regardless of MultiPV 4 or 8. The low
intervention rate was therefore caused primarily by the probability-to-score
conversion, not by candidate count.

## Candidate discrimination and robustness

The personal model's predicted-probability range across eight candidates
averaged 3.46 percentage points and had a 2.28-point median. Fifty-eight of 231
positions had less than a one-point spread, meaning that the model often sees
near-equivalent candidate difficulty.

Population and personal probabilities were correlated at 0.794, but their
highest-probability candidate differed in 64.1% of positions. This is evidence
that player-specific training materially changes candidate ranking, not evidence
that either ranking causes more human errors.

At the selected policy, lifetime-personal choices agreed with the time-decayed
model on 96.1% of positions, the recent-window model on 87.4%, and the population
model on 84.0%. Only 8 of 1,848 candidate rows (0.43%) exceeded any historical
train-plus-validation feature range, confined to mobility or legal-move count.
The candidate corpus is therefore largely in distribution, although tree-model
uncertainty is not directly quantified.

## Interpretation

The new policy increases experimental power by making personal interventions
roughly four times as frequent while retaining the existing 35 cp hard safety
boundary. It was selected entirely from model predictions, so it cannot count
as evidence that the model causes errors or wins games. Those claims remain for
the blinded prospective human experiment.

The complete grid and diagnostics are stored in
`benchmarks/adaptive_policy/validation_policy_sensitivity.json`.
