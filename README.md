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

### Future Stages

- Transposition table
- Move ordering
- Iterative deepening
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

Search a position at a fixed depth:

```powershell
python main.py --search-depth 4
python main.py --fen "..." --search-depth 4
```

## Goal

Build an adaptive chess engine capable of dynamically changing its play style based on opponent tendencies.
