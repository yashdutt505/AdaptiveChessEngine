# C++20 Production Core

This directory begins the production-core migration while Python remains the
correctness oracle and research harness.

The initial verified boundary contains the exact 32-bit packed-move layout and
the synchronized mailbox/piece-bitboard/occupancy representation used by the
Python engine.

Build the smoke test with a modern compiler:

```powershell
g++ -std=c++20 -O3 -Wall -Wextra -pedantic -Icpp/include cpp/tests/core_smoke.cpp -o cpp/core_smoke.exe
./cpp/core_smoke.exe
```

The currently available legacy MinGW toolchain can validate this initial
C++20-compatible subset with `-std=c++17`; production builds should use a
current C++20 compiler.

Completed oracle-checked ports now include FEN and hashing, make/unmake with all
special moves, legal move generation, and reference perft. The next production
ports are evaluation, transposition storage, and search.
