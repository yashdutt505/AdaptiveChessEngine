# Learned Adaptive Selector: Implementation and First Safety Results

## Frozen policy

The validation-selected lifetime personal histogram-gradient-boosting model and
the same-class population model are exported into deterministic C++ tree data.
The export records the source artifact SHA-256, exact 17-feature order, tree
thresholds, missing-value directions, and leaf values. C++ inference matches
sklearn probabilities to within `1e-12` on the parity corpus.

For every completed safe MultiPV candidate, the engine measures the position
after its move from the opponent's perspective and predicts the probability of
an opponent error of at least 100 cp on the next decision. The fixed adjustment
is:

```text
bonus_cp = clamp(round(100 * (candidate_probability - rank1_probability)), -20, 20)
adjusted_score = search_score + bonus_cp
```

The existing 35 cp eligibility bound, mate protection, completion requirement,
and neutral fallback remain authoritative. The random-safe control uses a
deterministic position-and-move hash in the same -20 to +20 cp range. No model
is updated during a game.

## Identical-candidate replay

Thirty-two chronologically held-out positions immediately before a historical
opponent of Yash moved were replayed at 20,000 target nodes. Thus each candidate
move led to a position in which Yash would be the vulnerable side to move. All
four policies consumed byte-for-byte equal move/score candidate lists: **zero
candidate mismatches**.

| Policy | Move changes | Change rate | Mean search-score loss | Maximum loss |
|---|---:|---:|---:|---:|
| Neutral rank 1 | 0 / 32 | 0.0% | 0.00 cp | 0 cp |
| Population model | 2 / 32 | 6.25% | 0.25 cp | 8 cp |
| Personal lifetime model | 1 / 32 | 3.13% | 0.03 cp | 1 cp |
| Deterministic random-safe | 11 / 32 | 34.38% | 1.47 cp | 15 cp |

The personal policy is working but conservative under the frozen 100 cp scale:
it rarely finds a predicted-probability improvement large enough to offset even
a small search-score disadvantage. This is a useful measured design property,
not evidence of match advantage.

## Engine-opponent safety match

Each arm played 16 games against Stockfish 18 limited to 1164, with the same
eight openings, swapped colors, 20,000 target nodes per move, MultiPV 4, one
process per engine, and 30 ms reference moves.

| Policy | W-D-L | Score | Score difference from neutral | 95% paired bootstrap interval |
|---|---:|---:|---:|---:|
| Neutral | 11-5-0 | 84.38% | - | - |
| Population | 11-4-1 | 81.25% | -3.13 pp | -21.88 to +15.63 pp |
| Personal | 12-4-0 | 87.50% | +3.13 pp | -12.50 to +18.75 pp |
| Random-safe | 9-6-1 | 75.00% | -9.38 pp | -28.13 to +6.25 pp |

All intervals include zero. The run found no detectable strength difference and
is too small for an Elo claim. It verifies legality, stability, bounded
selection, and compute parity. Stockfish at the same approximate rating is not
Yash and does not express Yash's learned tendencies, so this is **not** the
causal test of personalization.

## Remaining causal test

The research claim requires prospective games against the profiled person after
the policies and analysis plan are frozen. Yash must face neutral, population,
personal, and random-safe arms under blinded, randomized, color-balanced
conditions. A historical game cannot supply Yash's response after the engine
chooses a different move, and an ordinary chess engine is not a valid proxy for
his behavior. A separately validated behavioral simulator could be an
additional experiment, but cannot replace the human result.

Machine-readable results are in `benchmarks/adaptive_policy/`.
