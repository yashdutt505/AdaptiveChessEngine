# Adaptive Chess Engine

A chess engine built from scratch, with a performance-oriented C++ core and a
Python reference implementation, test harness, and research environment.

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
- Reference-oracle comparison across deterministic random games
- Static exchange evaluation and losing-capture quiescence pruning
- Countermove ordering and history maluses
- Tapered piece mobility evaluation
- Deterministic UCI node limits and configurable move overhead
- Deterministic self-play and EPD best-move strength runners
- Independently playable C++ engine with legal move generation, tapered
  evaluation, clustered transposition storage, PVS search, and fixed-depth UCI

### Future Stages

- Static exchange evaluation and staged move ordering
- Late-move reductions and safe pruning after self-play validation
- C++ time management, interruptible search, and remaining search heuristics
- Adaptive evaluation

## Verification

Run the automated suite:

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

Build the standalone C++ engine with:

```powershell
g++ -std=c++20 -O3 -Icpp/include cpp/src/main.cpp -o cpp/adaptive_chess_engine.exe
```

The C++ executable currently supports fixed-depth UCI searches. Python remains
the full protocol reference for move-time, clock-managed, node-limited, and
interruptible searches.

Run the engine in UCI mode with:

```powershell
python main.py
```

On Windows, `run_engine.bat` locates Python and starts the Python UCI process.
Add that launcher as a UCI engine in a compatible GUI. The engine supports `position`,
`go depth`, `go movetime`, clock-based `go`, `stop`, and `quit`.

## Goal

Build an adaptive chess engine capable of dynamically changing its play style based on opponent tendencies.
