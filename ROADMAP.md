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
- [x] Reused undo-state records by search ply
- [ ] Incremental material, phase, and piece-square evaluation

## Stage 15 - Search Strength

- [x] Static exchange evaluation
- [x] SEE-ranked capture ordering
- [x] Countermove ordering and history maluses
- [x] Conservative quiescence delta and SEE pruning
- [ ] Validated late-move reductions
- [ ] Null-move pruning with zugzwang safeguards
- [ ] Futility and reverse-futility pruning
- [x] Clustered transposition table

## Stage 16 - Strength Measurement

- [x] EPD tactical and positional test runner
- [x] Deterministic fixed-node UCI search support
- [x] Fixed-node automated self-play
- [ ] SPRT-based change validation
- [ ] Known Elo baseline against external engines

## Stage 16A - Evaluation Expansion

- [x] Tapered minor and major piece mobility
- [ ] Threats and hanging pieces
- [ ] Outposts, space, and weak squares
- [ ] King attack zones and safe checks
- [ ] Automated evaluation-weight tuning

## Stage 17 - Production Language Migration

- [x] Preserve Python as the reference implementation and research harness
- [x] Establish a build-verified C++ packed-move and bitboard core boundary
- [x] Port FEN, Zobrist hashing, reversible moves, legal generation, and perft
- [x] Cross-check C++ position hashes and reference perft against Python
- [x] Port tapered evaluation, clustered transposition storage, and PVS search
- [x] Add a standalone fixed-depth C++ UCI executable
- [ ] Port clock management, search limits, and asynchronous stop to C++
- [ ] Port or replace the remaining production search heuristics in C++
- [x] Keep adaptive modelling and tuning tools in Python

The adaptive layer starts only after Stages 14-17 produce a stable, measured base engine.
