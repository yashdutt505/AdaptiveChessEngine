# Adaptive Chess Engine

A chess engine built from scratch, with a performance-oriented C++ core and a
Python reference implementation, test harness, and research environment.

## Architecture

| Component | Role |
|---|---|
| C++ engine | Production UCI engine, legal moves, evaluation, search, timing, and self-play |
| Python engine | Independent correctness oracle, experiments, tuning, and future adaptive learning |

Python and C++ are both intentional parts of the project. Normal GUI games use
the C++ executable; Python verifies behavior and supports research workflows.

See the complete [architecture, known limitations, and adaptive-layer
roadmap](docs/ARCHITECTURE.md).

## Quick Start on Windows

From the repository folder, build the production engine once:

```powershell
.\build_cpp_engine.bat
```

This creates `cpp\adaptive_chess_engine.exe`. Test the executable directly:

```powershell
.\run_cpp_engine.bat
```

It will wait silently for UCI commands; that is normal. Type `uci` and press
Enter to see the handshake, then type `quit` to exit.

## Stage Progress

### Stage 1 - Complete

- Board representation and packed moves
- FEN parser
- Reversible make/unmake
- Castling, en passant, and promotion
- Undo history
- Incremental Zobrist hashing
- Position validation
- Automated regression tests

### Stage 2 - Complete

- Attack detection
- Pseudo-legal move generation
- Legal move filtering
- Perft and divide

### Stage 3 - Complete

- Static evaluation
- Terminal and draw detection
- Negamax alpha-beta search
- Quiescence search
- Principal variation reporting

### Stage 4 - Complete

- UCI protocol
- Iterative deepening
- Fixed depth and move-time searches
- Clock and increment time management
- Asynchronous `stop` support

### Stage 5 - Complete

- Transposition table
- Hash-move ordering
- Configurable UCI `Hash` option
- UCI `Clear Hash` button

### Stage 6 - Complete

- MVV-LVA capture ordering
- Killer-move heuristic
- History heuristic
- Cutoff statistics

### Stage 7 - Complete

- Tactical benchmark suite
- Fast production make/unmake path
- Tactical-only quiescence move generation
- Early legal-move detection

### Stage 8 - Complete

- Aspiration windows

### Stage 9 - Complete

- Tapered middlegame/endgame evaluation
- King shelter and castling safety
- Connected, passed, isolated, and doubled pawns
- Open and semi-open rook files
- Seventh-rank rooks and bishop pair

### Engine Core Optimization - Complete

- Repeatable perft and search performance baseline
- Bitboard piece iteration in move generation
- Precomputed king and knight attack tables
- Cached pawn-structure evaluation
- Bitboard-driven evaluation loops
- Principal variation search
- Direct legal generation using checker and absolute-pin masks
- Occupancy-indexed bishop, rook, and queen attack lookup tables
- Fixed-capacity move lists and principal-variation storage in recursive search
- Incremental C++ material, piece-placement, bishop-count, and phase state
- Aspiration-window C++ iterative deepening with automatic widening
- Reference-oracle comparison across deterministic random games
- Static exchange evaluation and losing-capture quiescence pruning
- Countermove ordering and history maluses
- Tapered piece mobility evaluation
- Deterministic UCI node limits and configurable move overhead
- Deterministic self-play and EPD best-move strength runners
- Independently playable C++ engine with legal move generation, tapered
  evaluation, clustered transposition storage, ordering, pruning, timed PVS,
  asynchronous UCI, self-play, and SPRT measurement

### Future Stages

- Multi-threaded search and broader positional evaluation
- Adaptive evaluation

## Verification

The first measured short-time baseline is approximately **1871 Elo on
Stockfish 18's limited-strength scale**. See
[`docs/ELO_BASELINE.md`](docs/ELO_BASELINE.md) for the protocol, uncertainty,
and reproduction command. This is a local engine-testing rating, not a human
FIDE, Chess.com, or Lichess rating.

Run the Python oracle suite:

```powershell
python -m unittest discover -v
```

Run perft from the starting position:

```powershell
python main.py --perft 4
python main.py --divide 3
```

Use `--fen "..."` to verify another position.

Run the tactical strength benchmark:

```powershell
python main.py --benchmark-depth 3
```

Run the deterministic move-generation and search speed baseline:

```powershell
python main.py --performance
```

Search a position at a fixed depth:

```powershell
python main.py --search-depth 4
python main.py --fen "..." --search-depth 4
```

## Using a Chess GUI

First run:

```powershell
.\build_cpp_engine.bat
```

Then open your UCI-compatible GUI and add a new engine. Select either:

- `cpp\adaptive_chess_engine.exe` directly; or
- `run_cpp_engine.bat` if the GUI accepts batch launchers.

Select the executable directly when possible. The C++ engine supports fixed
depth, move time, clock and increment management, node and mate limits,
`go infinite`, and asynchronous `stop`.

The existing `run_engine.bat` launches the Python reference engine. It remains
useful for comparison and testing, but is not the recommended playing launcher.

## C++ Toolchain

C++ is a language standard, not a runtime that must be downloaded separately.
You need a compiler. The source targets C++20 and retains C++17 compatibility
for the legacy MinGW GCC 6.3 compiler currently used by this workspace.

A modern 64-bit GCC, Clang, or Visual Studio C++ compiler is recommended for
continued development. Rebuilding with a newer compiler may improve generated
code and gives access to current C++20 tooling, but it is not required to play
the engine today.

## Python Reference Engine

Run the independent Python UCI implementation with:

```powershell
python main.py
```

On Windows, `run_engine.bat` locates Python and starts this reference process.

## Goal

Build an adaptive chess engine capable of dynamically changing its play style based on opponent tendencies.
