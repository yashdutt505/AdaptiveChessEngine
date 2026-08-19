# Adaptive Experiment and Safety Contract

## Hypothesis

A bounded selector can choose among objectively competitive root moves using a
versioned opponent profile, producing measurable behavioural differences and a
better match score than the same engine in neutral mode.

The adaptive layer is a root decision policy. It does not modify legality,
recursive search, evaluation, pruning, or time management.

## Modes and experimental unit

- **Neutral:** always play the highest-scoring completed root candidate.
- **Adaptive:** rerank only eligible completed root candidates using a fixed,
  preloaded profile and position features.
- The experimental unit is a color-swapped game pair from the same opening.
- Engine binary, search limits, opening set, hardware allocation, and random
  seed must be identical between neutral and adaptive arms.

## Safety invariants

1. Only legal moves returned by the C++ root search are selectable.
2. Neutral mode is the default and remains available through the entire game.
3. Missing, malformed, unsupported, non-finite, or out-of-range profile data
   fails closed to neutral mode before search begins.
4. Adaptation may choose only from completed MultiPV lines within a configured
   centipawn loss bound from the neutral best move. The initial bound is 35 cp.
5. Mate scores are never traded for centipawn preferences. A forced mate for
   the engine must be preserved; a line allowing a forced mate is ineligible.
6. No profile learning or mutation occurs during a rated game.
7. Fixed position, profile, engine version, limits, and seed must reproduce the
   same candidate set, selected move, and explanation.
8. Search interruption or incomplete candidate output falls back to the best
   result from the last fully completed iteration.

## Required decision record

Every adaptive choice must record: engine version, profile schema/version and
identifier, FEN or position hash, search limits, candidate rank/move/score/PV,
eligibility reason, feature values, bounded adaptive adjustment, neutral move,
selected move, and fallback reason when adaptation was not applied.

## Phased acceptance gates

1. **Candidate correctness:** MultiPV moves are legal, unique, score-sorted,
   deterministic under fixed limits, and leave the position unchanged.
2. **Neutral equivalence:** with adaptation disabled or a zero profile, move
   choices match neutral `MultiPV=1` on the regression corpus.
3. **Bound enforcement:** property tests prove no selected move violates the cp
   or mate constraints, including invalid-profile and interrupted-search cases.
4. **Behavioural signal:** synthetic profiles produce their intended directional
   differences on a labeled position suite without exceeding safety bounds.
5. **Strength experiment:** adaptive versus neutral uses color-swapped openings,
   reports W/D/L, Elo estimate and confidence interval (or SPRT), and is accepted
   only by a preregistered threshold. No tuning occurs on the final test set.

## Initial experiment defaults

- MultiPV candidate count: 4
- Maximum neutral score loss: 35 cp
- Profile fixed for a complete match
- Development positions, validation positions, and final match openings are
  separately versioned datasets
- All experiment configuration and results are saved as machine-readable data

Changes to these defaults must be versioned with the experiment configuration;
they must not silently change the meaning of prior results.

## MultiPV completion contract

The C++ root-candidate result records the requested candidate count, total legal
root moves, fully searched root moves, completed depth, and whether every legal
root move was compared. Candidate-specific nodes and elapsed time describe each
root search; result-level nodes and time describe the complete operation.

Only a result marked complete, with all legal root moves searched and a nonzero
completed depth, may be consumed by neutral or adaptive selection. Interrupted
results may contain diagnostic partial candidates, but they are never an
eligible decision set. Checkmate and stalemate are complete zero-candidate
results because the root position has no legal moves.
