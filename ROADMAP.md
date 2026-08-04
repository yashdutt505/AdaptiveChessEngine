# Adaptive Chess Engine Roadmap

## Stage 1 - Complete

- [x] Board representation
- [x] Move encoding
- [x] FEN parsing
- [x] Position make/unmake
- [x] Zobrist hashing
- [x] Validation
- [x] Automated regression tests

## Stage 2 - Complete

- [x] Attack maps
- [x] Pseudo-legal move generation
- [x] Legal move filtering

## Stage 3 - Complete

- [x] Perft
- [x] Divide
- [x] Reference-position verification

## Stage 4 - Complete

- [x] Evaluation
- [x] Draw detection

## Stage 5 - Complete

- [x] Negamax alpha-beta search
- [x] Quiescence search
- [x] Principal variation
- [x] Search regression tests

## Stage 6 - Complete

- [x] UCI protocol
- [x] Iterative deepening
- [x] Time management
- [x] Interruptible search
- [x] GUI launcher

## Stage 7 - Complete

- [x] Transposition table
- [x] Hash-move ordering
- [x] UCI Hash and Clear Hash controls

## Stage 8 - Complete

- [x] MVV-LVA capture ordering
- [x] Killer moves
- [x] History heuristic
- [x] Cutoff statistics

## Stage 9 - Complete

- [x] Tactical benchmark suite
- [x] Remove debug hashing from production search
- [x] Tactical-only quiescence generation
- [x] Search performance regression tests

## Stage 10 - Complete

- [x] Aspiration windows
- [x] Tactical regression safeguards

## Stage 11

- [x] Principal variation search
- [ ] Late-move reductions
- [ ] Null-move pruning

## Stage 12 - Complete

- [x] Tapered middlegame/endgame evaluation
- [x] King safety and pawn shields
- [x] Improved pawn structure
- [x] Rook file and seventh-rank bonuses
- [x] Strategic evaluation regression tests

## Stage 13 - Core Performance Foundation

- [x] Repeatable perft and search speed benchmark
- [x] Bitboard iteration for piece move generation
- [x] Precomputed knight and king attacks
- [x] Bitboard-driven evaluation loops
- [x] Cached pawn-structure evaluation

## Stage 14 - Production Move Core

- [x] Direct legal generation from checkers and pins
- [ ] Occupancy lookup attacks for sliding pieces
- [ ] Preallocated search state and move stacks
- [ ] Incremental material, phase, and piece-square evaluation

## Stage 15 - Search Strength

- [ ] Static exchange evaluation
- [ ] Staged move ordering
- [ ] Quiescence delta and SEE pruning
- [ ] Validated late-move reductions
- [ ] Null-move pruning with zugzwang safeguards
- [ ] Futility and reverse-futility pruning
- [ ] Clustered transposition table

## Stage 16 - Strength Measurement

- [ ] EPD tactical and positional test runner
- [ ] Fixed-node automated self-play
- [ ] SPRT-based change validation
- [ ] Known Elo baseline against external engines

## Stage 17 - Production Language Migration

- [ ] Preserve Python as the reference implementation and research harness
- [ ] Port the tested engine core to C++20
- [ ] Cross-check C++ perft, search, and evaluation against Python
- [ ] Keep adaptive modelling and tuning tools in Python

The adaptive layer starts only after Stages 14-17 produce a stable, measured base engine.
