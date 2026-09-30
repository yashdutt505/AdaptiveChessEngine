# Reference-label stability study

## Decision

Use Stockfish at **100,000 nodes per search**, one thread, cleared hash, for the
version-1 opponent-error corpus. Each decision requires one best-move search and
one forced-played-move search. Mate-score observations remain excluded.

This budget was chosen before model fitting. It is not assumed to be perfect:
the 50k-to-100k comparison still flips 12 of 453 jointly eligible binary labels.
All downstream claims must therefore treat the labels as noisy measurements.

## Data and method

- Player: `YashDutt7`
- Cohort: 1,182 Chess.com games with exact `TimeControl=600`
- Extracted corpus: 36,039 decisions from 1,166 usable games
- Archive PGN SHA-256:
  `d624add4160436e18a4c6e2bfd90c50c817ef4f799645c72c0465d4b6e4e2a6f`
- Stability sample: 500 decisions selected by the committed deterministic hash
  sampler, then retained in source order
- Error threshold: centipawn loss >= 100
- Engine configuration: Stockfish, one thread, MultiPV 1, 64 MB hash, hash
  cleared before every search

The sample and analyzed personal-game rows live under ignored `data/` paths and
are intentionally not committed. The selection and comparison code is tracked.

## Results

| Budgets compared | Jointly eligible | Binary agreement | Cohen's kappa | Label flips | Mean absolute CPL difference | Median absolute CPL difference | CPL Pearson r |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5k vs 20k | 468 | 94.44% | 0.7980 | 26 | 20.13 | 12 | 0.9549 |
| 5k vs 50k | 459 | 94.77% | 0.8128 | 24 | 23.45 | 12 | 0.9463 |
| 20k vs 50k | 459 | 96.73% | 0.8859 | 15 | 16.02 | 8 | 0.9745 |
| 50k vs 100k | 453 | 97.35% | 0.9071 | 12 | 12.67 | 7 | 0.9827 |

The number jointly eligible decreases at higher budgets because deeper searches
discover mate scores that version 1 excludes. The monotonic improvements in
agreement, kappa, absolute score difference, and correlation are evidence that
the labels are converging. They also reject the cheaper 5k budget: its roughly
5% threshold disagreement is avoidable measurement noise.

## Limits

This is a sensitivity analysis on one deterministic sample, not a confidence
interval for all positions. Node budgets are nested measurements from the same
engine, so their agreement does not establish correctness against independent
human annotations or another engine. A later robustness analysis should vary
the error threshold and, if conclusions are close, repeat key results with a
larger reference budget.
