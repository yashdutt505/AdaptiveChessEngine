# Tests

Current automated tests cover:

- FEN parsing and round trips
- Make/unmake and exact state restoration
- Captures, castling, promotion, and en passant
- Incremental Zobrist hashes
- Attack and check detection
- Pinned pieces and king safety
- Legal castling and en passant edge cases
- Standard perft reference positions
- Evaluation and draw rules
- Checkmate, stalemate, and tactical search
- Exact position restoration after search
- Iterative deepening and interruption
- UCI command parsing and asynchronous search
- Transposition-table storage, replacement, and reuse
- Killer and history move-ordering behavior
- Deterministic tactical benchmark positions

Run all tests with:

```powershell
python -m unittest discover -v
```

Future tests will cover transposition tables and advanced search heuristics.
