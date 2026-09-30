# YashDutt7 opponent-model results

## Bottom line

On future chronological games, the nonlinear personalized model predicts
`YashDutt7`'s >=100 cp errors better than the same model class trained on a
population sample. Linear personalization does not: both regularized logistic
and the partially pooled Bayesian logistic model are slightly worse than their
population fallbacks.

The selected deployment candidate is therefore histogram gradient boosting.
This is evidence for nonlinear, position-dependent personal tendencies. It is
not yet evidence that adaptive move selection wins more games at equal compute;
that requires prospective or precommitted proxy matches after integration.

## Corpus and protocol

- Chess.com exact 10-minute games: 1,182 downloaded; 1,166 usable
- Personal decisions: 36,039; eligible labels: 32,988
- Large errors: 5,726; mate-score exclusions: 3,051
- Chronological split: 695/235/236 train/validation/test games
- Eligible split rows: 18,317/7,193/7,478
- Population prior: 8,488 eligible opponent decisions from 300 deterministic
  whole-game train/validation samples
- Label: Stockfish, 100,000 nodes per best and forced-played search, one thread,
  cleared hash; centipawn loss >=100; mate observations excluded
- Selection: validation log loss only; final test inspected once
- Uncertainty: 2,000-replicate paired bootstrap over whole games
- Archive PGN SHA-256:
  `d624add4160436e18a4c6e2bfd90c50c817ef4f799645c72c0465d4b6e4e2a6f`

## Three-model comparison on untouched test games

| Personalized model | Log loss | Brier | ROC AUC | Average precision | ECE-10 |
|---|---:|---:|---:|---:|---:|
| Regularized logistic | 0.40499 | 0.12157 | 0.62550 | 0.21108 | 0.03020 |
| Hierarchical Bayesian logistic (Laplace) | 0.40471 | 0.12152 | 0.62584 | 0.21121 | 0.02968 |
| Histogram gradient boosting | **0.39348** | **0.11958** | **0.64934** | **0.22044** | **0.01608** |

Test prevalence is 14.44%. A constant training-prevalence predictor has log
loss 0.42123 and Brier score 0.12598. Gradient boosting beats regularized
logistic by -0.01151 log loss (95% game-bootstrap CI -0.01604 to -0.00714) and
beats hierarchical logistic by -0.01122 (-0.01568 to -0.00686).

## Does player-specific history add information?

The same model class was separately fit to personal history and population
history, then compared on identical personal test rows. Negative differences
favor personal training.

| Model class | Personal log loss | Population log loss | Difference | 95% game-bootstrap CI | Result |
|---|---:|---:|---:|---:|---|
| Regularized logistic | 0.40499 | 0.40299 | +0.00200 | +0.00025 to +0.00368 | population better |
| Hierarchical logistic | 0.40471 | 0.40291 | +0.00180 | +0.00038 to +0.00313 | population better |
| Gradient boosting | **0.39348** | 0.40004 | **-0.00656** | **-0.01081 to -0.00198** | personal better |

The bootstrap probability that personalized boosting is better is 99.9%. The
linear result points the other way: a fixed historical coefficient shift is too
rigid under substantial player improvement and is shrunk toward stale history.

## Post-hoc robustness and interpretation

These ablations were performed after the primary test and are exploratory, not
new confirmatory tests. Personalized boosting still beats population boosting:

| Excluded inputs | Log-loss difference | 95% game-bootstrap CI |
|---|---:|---:|
| Player rating and rating difference | -0.00546 | -0.00819 to -0.00269 |
| Fullmove number | -0.02246 | -0.03050 to -0.01436 |
| Both rating inputs and fullmove number | -0.00870 | -0.01205 to -0.00514 |

Thus the personalization gain is not explained solely by rating/era or move
number. The primary boosting model's post-hoc permutation ranking is led by
fullmove number, material imbalance, rating difference, legal-move count,
remaining pawns/material, and legal captures. Feature correlation makes this a
descriptive ranking, not a causal statement about why errors happen.

## What is established and what is not

Established:

- Position features predict future large errors better than a base rate.
- Nonlinear boosting materially outperforms both linear alternatives.
- For boosting, target-player history improves held-out prediction over a
  compute-identical population model, including without rating/time proxies.
- Linear personalization is counterproductive under this corpus's strong rating
  drift, an important negative result.

Not established:

- A personalized selector wins more games than neutral selection.
- The predictive gain transfers to different time controls, current games after
  June 2026, or another player.
- Post-hoc feature importance identifies causal weaknesses.
- A result from thousands of correlated moves equals thousands of independent
  observations; uncertainty is therefore clustered by game.

## Next confirmatory experiment

Freeze the boosting artifact and translate its exact feature/inference contract
into the C++ root selector. For every safe MultiPV candidate, predict the
opponent's next-move large-error probability and apply a preregistered bounded
bonus. Compare against a population-model selector and neutral rank-1 selector
with identical MultiPV candidates, nodes, openings, hardware, and colors. Do not
tune the bonus on the final match set. A real human test requires new blinded
games after the profile freeze; retrospective prediction cannot substitute for
that causal outcome.
