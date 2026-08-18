# Elo Benchmark

## Result

The latest reproducible measurement is **1996 Elo**, reasonably reported as
**approximately 2000 Elo**, on Stockfish 18's `UCI_LimitStrength` scale at
30 ms per move. A logistic maximum-likelihood fit across 112 games gives an
approximate 95% interval of **1930-2063**.

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

## Latest samples

| Stockfish setting | Games | W-D-L | Score | Single-sample estimate |
|---:|---:|---:|---:|---:|
| 1875 | 64 | 35-14-15 | 65.6% | 1987 |
| 2000 | 48 | 20-9-19 | 51.0% | 2007 |

The engine scored 66.5/112 (59.4%) overall. The combined maximum-likelihood
estimate is 1996, approximately **125 Elo above the previous 1871 baseline**.
The interval is approximate: time-based searches are noisy, opening pairs are
correlated, and maximum-ply draw adjudication is a testing convention. A
publication-quality rating should use hundreds or thousands of games, a larger
balanced opening suite, and at least two independent reference engines.

All 112 games completed without an engine crash or an illegal returned move.

## Historical baseline

The earlier 78-game measurement estimated 1871 Elo with an approximate
1792-1949 interval. It remains useful as the pre-optimization comparison point;
it is not combined with the latest samples because it measured an older engine
revision.

## Reproduce

The official Stockfish binary is deliberately Git-ignored. Supply paths to the
built C++ engine and a local Stockfish executable:

```powershell
python tools/elo_match.py `
  --target cpp/adaptive_chess_engine.exe `
  --reference path/to/stockfish.exe `
  --opponent-elo 2000 `
  --games 48 `
  --movetime 30 `
  --max-plies 140 `
  --output benchmarks/elo/match.json
```

Future engine changes should first pass unit/perft/tactical gates, then be
measured candidate-versus-baseline with SPRT. The Stockfish gauntlet should be
rerun for release-level absolute baselines.
