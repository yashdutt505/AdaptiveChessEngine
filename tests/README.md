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

Run all tests with:

```powershell
python -m unittest discover -v
```

Search tests will be added with the search stage.
