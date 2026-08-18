# C++20 Production Core

This directory contains the production UCI engine. Python remains alongside it
as the independent correctness oracle, tuning environment, and research harness.

The C++ implementation includes the exact 32-bit packed-move layout and the
synchronized mailbox/piece-bitboard/occupancy representation cross-checked
against the Python implementation.

Build the smoke test with a modern compiler:

```powershell
g++ -std=c++20 -O3 -Wall -Wextra -pedantic -Icpp/include cpp/tests/core_smoke.cpp -o cpp/core_smoke.exe
./cpp/core_smoke.exe
```

The currently available legacy MinGW toolchain can validate this initial
C++20-compatible subset with `-std=c++17`; production builds should use a
current C++20 compiler.

From the repository root, build the standalone UCI engine with:

```powershell
.\build_cpp_engine.bat
```

Completed oracle-checked ports now include FEN and hashing, make/unmake with all
special moves, direct checker/pin legal move generation, occupancy-indexed
sliding attacks, fixed recursive move/PV storage, incremental base evaluation,
reference perft, tapered evaluation, clustered transposition storage,
aspiration-window iterative deepening, quiescence and principal-variation search, and
a standalone UCI executable with clock, increment, move-time, node and mate
limits plus asynchronous `stop` and `go infinite` support.

Python remains intentionally available as the correctness oracle, benchmark and
research harness, and future adaptive-layer environment. The C++ executable is
the performance-oriented engine path; deleting Python is not a migration goal.

Build and run the deterministic self-play/SPRT strength tool with:

```powershell
g++ -std=c++20 -O3 -Icpp/include cpp/tools/selfplay.cpp -o cpp/selfplay.exe
./cpp/selfplay.exe 20 3 160
```

The arguments are games, fixed depth, and maximum plies. Games alternate the
candidate's color; the summary reports W/D/L and the running 0-versus-10 Elo
score-SPRT likelihood ratio.

The requested production migration path is now complete: C++ owns UCI, time
management, position state, legal moves, evaluation, ordering, search, pruning,
and strength measurement. Python remains on purpose as an independent oracle,
tuning environment, and the home of the future adaptive-learning workflow.
