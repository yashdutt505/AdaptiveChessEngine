# Opponent-error model features

Feature set `ace.opponent-error-position.v1` predicts whether the side to move
will lose at least 100 centipawns. It is distinct from the older synthetic
profile schema: these fields are model inputs, not hand-authored preferences.

All balance fields use the vulnerable side-to-move player's perspective. During
training that side is `YashDutt7`; during deployment it is the opponent in the
position produced by one of the engine's root candidates. This makes training
and inference semantics identical.

The version-1 inputs are current check status; counts of legal moves and legal
captures; material balance and absolute imbalance; remaining non-pawn material,
pawns, and open files; mobility, king-safety, pawn-structure, and centre-control
balances; pawn tensions; fullmove number; side-to-move colour; player rating;
and rating difference.

No Stockfish evaluation, played-move result, centipawn loss, game result, or
future information is an input. Rating missingness maps to zero in version 1;
the personal Chess.com corpus has ratings, so this is an inference fallback and
not expected during fitting.
