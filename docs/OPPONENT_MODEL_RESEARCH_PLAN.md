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

A neural network is not the default endpoint. It becomes justified only if the
dataset is large enough and it outperforms these calibrated baselines on held-out
players and prospective matches.

## Step 1: compute-matched control

Both experimental arms use `MultiPV=4`, the same time/node limit, and the same
all-root C++ search:

- Control: `Adaptive Mode=false`; always select MultiPV rank 1.
- Treatment: `Adaptive Mode=true`; apply the fixed opponent profile.

The adaptive engine internally enforces at least four candidates. Experiments
must explicitly set `MultiPV=4` for the control. The Elo harness accepts repeated
`--target-option NAME=VALUE` arguments and records them in its JSON result.

Single-PV neutral matches must not be used to estimate the causal adaptive gain.

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
