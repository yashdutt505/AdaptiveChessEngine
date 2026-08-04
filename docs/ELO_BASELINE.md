# Elo Baseline

## Result

The first reproducible baseline is **1871 Elo** on Stockfish 18's
`UCI_LimitStrength` scale at 30 ms per move. A logistic maximum-likelihood fit
across 78 games gives an approximate 95% interval of **1792-1949**.

This is not a FIDE, Chess.com, Lichess, CCRL, or CEGT rating. Ratings only have
meaning within a pool and testing protocol. This number is the engine's local
short-time baseline against Stockfish 18's calibrated UCI strength settings.

## Protocol

- Target: `Adaptive Chess Engine C++`, single process, 64 MB hash
- Reference: official Stockfish 18 AVX2, one thread, 64 MB hash
- Reference strength: Stockfish `UCI_LimitStrength=true`
- Time: 30 ms per move for the main samples
- Openings: eight deterministic four-ply openings
- Colors: every opening is replayed with colors swapped
- Maximum length: 140 plies, then adjudicated as a draw
- Validation: every returned move is checked by the Python legal-move oracle
- Draws: repetition, fifty-move, insufficient material, or maximum plies

## Samples

| Stockfish setting | Games | W-D-L | Score | Single-sample estimate |
|---:|---:|---:|---:|---:|
| 1320 | 2 | 2-0-0 | 100.0% | Bracketing only |
| 1800 | 4 | 2-1-1 | 62.5% | 1889 |
| 1900 | 24 | 9-4-11 | 45.8% | 1871 |
| 1875 | 48 | 19-9-20 | 49.0% | 1868 |

The combined maximum-likelihood estimate is 1871. The interval is approximate:
time-based searches are noisy, opening pairs are correlated, and maximum-ply
draw adjudication is a testing convention. A publication-quality rating should
use hundreds or thousands of games, a larger balanced opening suite, and at
least two independent reference engines.

## Reproduce

The official Stockfish binary is deliberately Git-ignored. Supply paths to the
built C++ engine and a local Stockfish executable:

```powershell
python tools/elo_match.py `
  --target cpp/adaptive_chess_engine.exe `
  --reference path/to/stockfish.exe `
  --opponent-elo 1875 `
  --games 48 `
  --movetime 30 `
  --max-plies 140 `
  --output benchmarks/elo/match.json
```

Future engine changes should first pass unit/perft/tactical gates, then be
measured candidate-versus-baseline with SPRT. The Stockfish gauntlet should be
rerun for release-level absolute baselines.
