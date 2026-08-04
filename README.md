# Adaptive Chess Engine

A chess engine built completely from scratch in Python.

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

### Future Stages

- Principal variation search and safe pruning after further benchmarking
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

Run the engine in UCI mode with:

```powershell
python main.py
```

On Windows, `run_engine.bat` locates Python and starts the same UCI process.
Add that launcher as a UCI engine in a compatible GUI. The engine supports `position`,
`go depth`, `go movetime`, clock-based `go`, `stop`, and `quit`.

## Goal

Build an adaptive chess engine capable of dynamically changing its play style based on opponent tendencies.
