"""
castling.py

Castling constants and update masks.
"""

from .squares import *

# ---------------------------------------
# Castling Rights
# ---------------------------------------

WHITE_KINGSIDE  = 1
WHITE_QUEENSIDE = 2
BLACK_KINGSIDE  = 4
BLACK_QUEENSIDE = 8

ALL_CASTLING_RIGHTS = (
    WHITE_KINGSIDE
    | WHITE_QUEENSIDE
    | BLACK_KINGSIDE
    | BLACK_QUEENSIDE
)

# ---------------------------------------
# Update masks
# ---------------------------------------

CASTLING_MASK = [ALL_CASTLING_RIGHTS] * 64

# White king
CASTLING_MASK[E1] &= ~(WHITE_KINGSIDE | WHITE_QUEENSIDE)

# Black king
CASTLING_MASK[E8] &= ~(BLACK_KINGSIDE | BLACK_QUEENSIDE)

# White rooks
CASTLING_MASK[A1] &= ~WHITE_QUEENSIDE
CASTLING_MASK[H1] &= ~WHITE_KINGSIDE

# Black rooks
CASTLING_MASK[A8] &= ~BLACK_QUEENSIDE
CASTLING_MASK[H8] &= ~BLACK_KINGSIDE