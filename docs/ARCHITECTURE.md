# Adaptive Chess Engine Architecture

This project uses a hybrid architecture. C++ owns the performance-critical
playing engine, while Python remains the independent correctness oracle,
measurement environment, tuning system, and future opponent-modelling layer.

## System architecture

```mermaid
flowchart TB
    GUI["BanksiaGUI / UCI-compatible GUI"]

    subgraph CPP["C++ production engine"]
        UCI["UCI interface<br/>commands, clocks, stop"]
        POS["Position core<br/>board, FEN, Zobrist hash"]
        MOVE["Move generation<br/>checker/pin masks, lookup attacks"]
        SEARCH["Search<br/>aspiration, PVS, quiescence"]
        ORDER["Move ordering<br/>TT, SEE, killers, history, countermoves"]
        PRUNE["Pruning<br/>LMR, null move, futility"]
        EVAL["Tapered evaluation<br/>material, mobility, pawns, king safety"]
        TT["Clustered transposition table"]
    end

    subgraph PY["Python research and validation"]
        ORACLE["Correctness oracle<br/>perft, hashes, legal moves"]
        TESTS["Regression tests<br/>automated correctness gates"]
        TUNING["Evaluation tuning and experiments"]
        MATCH["Strength measurement<br/>self-play, Stockfish, SPRT"]
        MODEL["Opponent model<br/>error-probability learning"]
    end

    subgraph DATA["Bridge and persistent data"]
        PROFILE["Future adaptive profile<br/>versioned and bounded"]
        GAMES["PGN / game history"]
        RESULTS["Benchmark and match results"]
    end

    GUI <-->|"UCI"| UCI
    UCI --> POS
    UCI --> SEARCH
    SEARCH --> MOVE
    SEARCH --> ORDER
    SEARCH --> PRUNE
    SEARCH --> EVAL
    SEARCH <--> TT
    MOVE <--> POS
    EVAL --> POS

    ORACLE -.->|"cross-checks"| POS
    ORACLE -.->|"cross-checks"| MOVE
    TESTS -.->|"guards"| SEARCH
    MATCH --> RESULTS
    MATCH -->|"plays"| UCI

    GUI --> GAMES
    GAMES --> MODEL
    MODEL --> PROFILE
    TUNING --> PROFILE
    PROFILE -.->|"future: load before game"| EVAL
    PROFILE -.->|"future: bounded root strategy"| SEARCH
```

Python will not be called at every search node. Python will learn and export a
small, validated profile; C++ will apply its bounded parameters without adding
inter-process overhead to the search tree.

## Current responsibility boundaries

| Area | Implementation | Status |
|---|---|---|
| GUI communication | C++ UCI executable | Playable in BanksiaGUI |
| Position and chess rules | C++ production core | Direct legality, perft and oracle checked |
| Search | C++ | Aspiration windows, PVS, quiescence and iterative deepening |
| Search efficiency | C++ | TT, SEE, ordering, LMR, null move and futility |
| Sliding attacks | C++ | Occupancy-indexed lookup tables used by generation, SEE and mobility |
| Recursive move storage | C++ | Fixed-capacity move lists and PV lines |
| Base evaluation state | C++ | Incremental material, placement, bishop counts and phase |
| Time management | C++ | Clocks, increments, limits and asynchronous stop |
| Correctness oracle | Python | Legal-move, hash, perft and regression checks |
| Strength measurement | C++ and Python | Self-play, SPRT and Stockfish gauntlets |
| Evaluation research | Python | Experiments and future automated tuning |
| Opponent modelling | Python | Research target and label defined; dataset/model pending |
| Adaptive profile execution | C++ | Bounded root selector with neutral fallback and synthetic profiles |

## Current limitations

1. **Partially dynamic evaluation.** Material, placement, bishop counts, and
   phase are incremental, but pawn structure, mobility, rook files, and king
   safety are still calculated at leaves because they depend on wider geometry.
2. **Limited positional knowledge.** Threats, outposts, space, weak squares,
   king attack zones, safe checks, and specialized endgames need expansion.
3. **Pruning validation scale.** Current reference comparisons pass, but LMR,
   null-move, and futility logic need much larger randomized and tactical sets.
4. **Measured strength baseline.** The latest 112-game gauntlet estimates 1996
   (approximately 2000) on Stockfish 18's limited-strength scale, with an
   approximate 1930-2063 interval. This is about 125 Elo above the earlier
   1871 baseline; it is not a FIDE or online-platform rating.
5. **Single-threaded search.** Lazy SMP and a UCI `Threads` option are not yet
   implemented.
6. **Synthetic-only adaptive bridge.** The C++ selector currently exposes the
   versioned synthetic profiles through UCI; learned PGN profiles and a general
   validated profile-file loader remain pending.

## Road to the adaptive layer

```mermaid
flowchart LR
    A["Completed: direct legality,<br/>lookups, move stacks"]
    B["Completed: incremental base<br/>evaluation and aspiration"]
    D["Broader tactical and<br/>pruning validation"]
    E["Stronger neutral<br/>evaluation"]
    F["500+ game<br/>multi-engine baseline"]
    G["Versioned adaptive<br/>profile schema"]
    H["Python analysis and<br/>C++ profile loader"]
    I["Opponent<br/>modelling"]
    J["Adaptive versus neutral<br/>SPRT validation"]

    A --> B --> D --> E --> F --> G --> H --> I --> J
```

### Acceptance principle

The adaptive layer begins only after the neutral engine is stable enough to
separate real behavioural adaptation from ordinary engine defects. Every
adaptive change must remain bounded, preserve chess legality, retain a neutral
fallback, and demonstrate value through color-swapped candidate-versus-neutral
SPRT matches.
