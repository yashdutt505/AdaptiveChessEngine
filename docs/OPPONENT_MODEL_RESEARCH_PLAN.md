# Opponent-Modelling Research Plan

## Research question

Can an opponent-conditioned engine score better than an otherwise identical
neutral engine when both receive the same root candidates, compute budget,
openings, hardware, and prior information boundary?

The primary comparison is personalized adaptive selection versus compute-matched
neutral selection. Ordinary single-PV play remains a practical strength baseline
but is not the causal control because it performs less root work.

## Model progression

1. **Regularized logistic regression:** first baseline predicting the probability
   that the opponent loses at least 100 cp on their next decision. It is easy to
   inspect, calibrate, reproduce, and connect to profile confidence.
2. **Gradient-boosted trees:** nonlinear challenger for thresholds and feature
   interactions after enough labeled data exists.
3. **Hierarchical Bayesian logistic model:** intended final personalized model.
   Population coefficients provide a prior; player-specific deviations are
   partially pooled, preventing small histories from producing extreme profiles.
   Posterior uncertainty controls confidence and neutral fallback.

The implemented third model uses a population coefficient vector plus a
Yash-specific deviation vector with a zero-centred Gaussian prior. Its prior
scale is selected on the personal chronological validation split. A Gaussian
Laplace approximation at the posterior mode supplies parameter uncertainty to
the predictive probabilities. This is computationally reproducible partial
pooling, but it is not full MCMC; that limitation must accompany reported
results.

The population component uses all opponent decisions from 300 deterministically
hashed train/validation games in the same archive. Sampling is by whole game,
not by decision, and test games are excluded. The roughly 9,000 expected rows
are sufficient to estimate a low-dimensional population logistic prior without
paying to label every opponent move; all personal Yash decisions remain in the
primary corpus.

Held-out probability comparisons use a paired bootstrap over whole games (2,000
replicates), preserving within-game dependence. Reports include 95% percentile
intervals for log-loss and Brier-score differences. The hierarchical report
also compares its personalized prediction with the same fitted model's
population-only fallback on identical Yash test positions; this is the first
direct test of whether player identity adds information.
Each non-hierarchical model class is also fit to the population sample using its
own chronological validation rows, then evaluated on the identical personal
test rows. Paired game-level comparisons between target-trained and
population-trained versions isolate the value of historical player-specific
training from the value of general chess-position features.

A neural network is not the default endpoint. It becomes justified only if the
dataset is large enough and it outperforms these calibrated baselines on held-out
players and prospective matches.

The personal-model runner selects logistic regularization and tree complexity
only by validation log loss, refits the chosen configuration on train plus
validation, and evaluates the chronological test split once. It reports log
loss, Brier score, ROC AUC, average precision, and 10-bin calibration error
against a constant train-prevalence baseline. Dependencies are pinned in
`requirements-research.txt`; generated model artifacts remain ignored.

## Step 1: compute-matched control

Both experimental arms use `MultiPV=4`, the same time/node limit, and the same
all-root C++ search:

- Control: `Adaptive Mode=false`; always select MultiPV rank 1.
- Treatment: `Adaptive Mode=true`; apply the fixed opponent profile.

The adaptive engine internally enforces at least four candidates. Experiments
must explicitly set `MultiPV=4` for the control. The Elo harness accepts repeated
`--target-option NAME=VALUE` arguments and records them in its JSON result.

Single-PV neutral matches must not be used to estimate the causal adaptive gain.

This was the initial learned-policy development control. The final prospective
policy was subsequently selected on chronological validation candidates only
and uses `MultiPV=8`, a 400 cp probability scale, and a 35 cp bonus cap. All
prospective arms, including neutral, must use MultiPV 8.

Example control options:

```powershell
--target-option "MultiPV=4" --target-option "Adaptive Mode=false"
```

Example treatment options:

```powershell
--target-option "MultiPV=4" --target-option "Adaptive Mode=true" `
--target-option "Adaptive Profile=synthetic-tactical-pressure-v1"
```

## Step 2: prediction target v1

For an opponent decision, a fixed reference analysis produces:

- `best_score_cp`: score of the reference-best move.
- `played_score_cp`: score after forcing the opponent's played move and analyzing
  it with the same reference settings.

Both values are converted to the opponent's perspective immediately before the
move. The supervised target is:

```text
centipawn_loss = max(0, best_score_cp - played_score_cp)
large_error = centipawn_loss >= 100
```

Version 1 excludes mate-score observations because mate distances are not stable
centipawn quantities. They will receive a separate categorical target later.
The dataset must store label version, threshold, raw loss, eligibility, and any
exclusion reason so the target cannot change silently.

## Step 3: chronological PGN extraction

`engine/pgn_dataset.py` parses standard PGN without an external chess library,
resolves SAN against the project's legal move generator, and records only the
target player's decisions. Every record contains the exact pre-move FEN, played
SAN and UCI move, game identity/date, opponent, color, move number, ratings,
time control, result, and dataset version.

Games are ordered chronologically and assigned whole to 60% train, 20%
validation, and 20% final test partitions. No positions from one game can cross
a split. Comments, NAGs, clock annotations, and side variations are ignored;
illegal or ambiguous SAN fails closed instead of corrupting the dataset.

## Step 4: fixed-reference analysis

`engine/reference_analysis.py` runs a UCI reference engine with one thread,
fixed nodes, fixed hash, and MultiPV 1. Hash is cleared before every call so a
position's label cannot depend on earlier dataset rows. It analyzes the original
position for the best score, then forces the played move and analyzes the child
position with the same node budget. The child score is negated back to the
player's pre-move perspective before label v1 is applied.

Every output row records the reference engine identity, analysis version, node
budget, best move, raw best/played scores, mate values, centipawn loss, binary
label, eligibility, and exclusion reason. Dataset moves are independently
checked for legality before the external engine is called.
Long reference runs append and flush one record at a time. Passing `--resume`
continues only when saved rows are an exact input prefix with the same analysis
version and node budget; mismatches fail closed.
Reference searches use a generous node-scaled wall-clock timeout solely as a
hang detector. Timeout length does not alter the fixed node budget or labels.
`--sample-size` selects a deterministic pseudo-random subset spanning the input,
and `tools/compare_reference_runs.py` quantifies label agreement, Cohen's kappa,
centipawn-loss correlation, and absolute disagreement between node budgets.
The preregistered corpus budget is 100,000 nodes per search; the empirical basis
and residual label noise are recorded in `docs/REFERENCE_LABEL_STABILITY.md`.

## Experimental safeguards

- Split games chronologically into train, validation, and untouched final test.
- Keep all positions from one game in the same split.
- Freeze the opponent and profile before prospective test matches.
- Compare personalized, population, wrong-player, random-safe, and neutral arms.
- Use paired openings with colors swapped and report Elo difference with an
  interval or SPRT, not only raw win rate.
- Measure calibration and error prediction before claiming match exploitation.

## Personal Chess.com corpus

`tools/download_chesscom_games.py` uses Chess.com's read-only public archive API
with an identifying User-Agent, caches each monthly JSON response, deduplicates
games by UUID/URL, and emits all-game, standard-chess, rapid, and exact 10-minute
PGN cohorts plus a hash-bearing manifest. Raw games, processed datasets, and
trained model artifacts are deliberately Git-ignored; code, schemas, aggregate
manifests, and reproducible research results belong in version control.

## Current research status

- [x] Download and hash the exact 10-minute personal corpus.
- [x] Validate and lock the 100,000-node labeling budget.
- [x] Label all 36,039 personal decisions with exact-cover shard validation.
- [x] Build the versioned, leakage-resistant feature matrix.
- [x] Compare regularized logistic, gradient boosting, and hierarchical
  Bayesian logistic models on chronological held-out games.
- [x] Compare personal training with same-class population fallbacks using
  paired game-level uncertainty.
- [x] Compare lifetime, recent-window, time-decayed, and 20-game online updates;
  retain lifetime boosting as the validation-selected frozen strategy.
- [x] Freeze and export the lifetime personal and population boosting models;
  verify sklearn-to-C++ inference and Python-to-C++ feature parity.
- [x] Integrate a preregistered, bounded probability bonus into safe MultiPV
  root selection, plus a deterministic random-safe control.
- [x] Run an identical-candidate replay and a preliminary compute-matched
  neutral, population, personalized, and random-safe engine-opponent match.
- [x] Select the final conversion policy on validation candidates, calibrate a
  5,000-node human-match setting, and preregister the blinded schedule.
- [ ] Complete the excluded pilot and 160-game prospective human evaluation.

Aggregate results and limits are reported in `docs/YASHDUTT7_MODEL_RESULTS.md`.
The player-history experiment is reported in
`docs/PLAYER_HISTORY_STRATEGY_RESULTS.md`.
The frozen selector and preliminary playing results are reported in
`docs/LEARNED_ADAPTIVE_SELECTOR_RESULTS.md`.
Validation-only policy selection is reported in
`docs/POLICY_SENSITIVITY_RESULTS.md`; the locked human protocol is in
`docs/PROSPECTIVE_HUMAN_EXPERIMENT.md`.
