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

Run all tests with:

```powershell
python -m unittest discover -v
```

UCI protocol tests will be added with the protocol stage.
