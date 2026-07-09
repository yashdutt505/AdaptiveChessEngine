"""
constants.py

Engine-wide constants.
"""

# ==========================================================
# Colors
# ==========================================================

WHITE = 0
BLACK = 1

# ==========================================================
# Castling Rights (bit flags)
# ==========================================================

WHITE_KINGSIDE  = 1 << 0   # 0001
WHITE_QUEENSIDE = 1 << 1   # 0010
BLACK_KINGSIDE  = 1 << 2   # 0100
BLACK_QUEENSIDE = 1 << 3   # 1000

ALL_CASTLING_RIGHTS = (
    WHITE_KINGSIDE
    | WHITE_QUEENSIDE
    | BLACK_KINGSIDE
    | BLACK_QUEENSIDE
)

# ==========================================================
# Misc
# ==========================================================

NO_EN_PASSANT = -1

START_FEN = (
    "rnbqkbnr/"
    "pppppppp/"
    "8/"
    "8/"
    "8/"
    "8/"
    "PPPPPPPP/"
    "RNBQKBNR "
    "w "
    "KQkq "
    "- "
    "0 "
    "1"
)