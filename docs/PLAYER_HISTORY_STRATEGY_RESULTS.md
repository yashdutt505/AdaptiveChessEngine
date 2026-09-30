# Player-history strategy comparison

## Question

Does an evolving-player profile predict future `YashDutt7` errors better when
it uses all history, only recent games, recency weights, or periodic online
updates?

The five arms use the same histogram-gradient-boosting model class and feature
contract. Window sizes and decay rates were selected on the chronological
validation split only. The final 236-game test period was not used for those
choices. Uncertainty uses a 2,000-replicate paired bootstrap over whole games.

## Selection and update rules

- Population model: the existing model trained on the deterministic population
  sample.
- Lifetime personal: all 930 personal train and validation games.
- Recent personal: the latest 200 games; 100, 200, and 300 were compared on
  validation.
- Time-decayed personal: all history with a 400-game half-life; half-lives of
  50, 100, 200, and 400 were compared on validation.
- Online personal: begin with the validation-selected lifetime strategy,
  predict the next 20-game batch, then add that completed batch and retrain.
  No future batch labels are visible at prediction time.

Lifetime personal had the best validation log loss (0.41206), ahead of the best
decay (0.41507) and recent-window (0.41804) candidates, so it is the frozen
strategy for the subsequent causal selector experiment.

## Untouched chronological test results

| Strategy | Log loss | Brier | ROC AUC | Average precision | ECE-10 |
|---|---:|---:|---:|---:|---:|
| Population | 0.40004 | 0.12122 | 0.62223 | 0.19859 | 0.01442 |
| Lifetime personal | **0.39348** | **0.11958** | 0.64934 | 0.22044 | 0.01608 |
| Recent 200-game personal | 0.40185 | 0.12116 | 0.64797 | 0.21606 | 0.03632 |
| Time-decayed personal | 0.39768 | 0.12048 | 0.64526 | 0.21762 | 0.02953 |
| Online personal, 20-game updates | **0.39048** | **0.11897** | **0.66229** | **0.22382** | 0.01630 |

Lifetime personal beats population by -0.00656 log loss (95% game-bootstrap
interval -0.01081 to -0.00198). Online updating beats population by -0.00956
(-0.01343 to -0.00543). Recent-window performance is not distinguishable from
population, and the selected lifetime model clearly beats both the recent and
decayed frozen variants on this test.

## Interpretation

The original hypothesis that old games necessarily damage the profile is not
supported for this model and corpus. Removing old games reduces sample size and
calibration enough to outweigh the benefit of recency. Gentle time decay is
better than a hard 200-game cutoff but still worse than lifetime training.

Concept drift nevertheless matters: online updating produces the best forward
prediction while respecting the information boundary. The correct conclusion
is therefore not “discard old games,” but “retain the broad lifetime signal and
refresh it as new labeled games arrive.” Online updating is a process rather
than a single frozen artifact; the lifetime model remains the fair frozen model
for the next compute-matched playing experiment.

The online result assumes labels can be produced after each completed batch by
the same 100,000-node Stockfish analysis. It does not imply that the C++ engine
can learn immediately during a game, and it is not yet evidence of more wins.
