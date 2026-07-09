"""
pieces.py

Defines every chess piece and helper functions.
"""

from enum import IntEnum
from .constants import WHITE, BLACK



# ==========================================================
# Pieces
#
# 0 MUST always mean EMPTY.
# The remaining 12 values map directly to bitboards.
# ==========================================================

class Piece(IntEnum):

    EMPTY = 0

    WHITE_PAWN = 1
    WHITE_KNIGHT = 2
    WHITE_BISHOP = 3
    WHITE_ROOK = 4
    WHITE_QUEEN = 5
    WHITE_KING = 6

    BLACK_PAWN = 7
    BLACK_KNIGHT = 8
    BLACK_BISHOP = 9
    BLACK_ROOK = 10
    BLACK_QUEEN = 11
    BLACK_KING = 12


# ==========================================================
# Piece Characters
#
# Used by FEN and board printing.
# ==========================================================

PIECE_TO_CHAR = {

    Piece.EMPTY: ".",

    Piece.WHITE_PAWN: "P",
    Piece.WHITE_KNIGHT: "N",
    Piece.WHITE_BISHOP: "B",
    Piece.WHITE_ROOK: "R",
    Piece.WHITE_QUEEN: "Q",
    Piece.WHITE_KING: "K",

    Piece.BLACK_PAWN: "p",
    Piece.BLACK_KNIGHT: "n",
    Piece.BLACK_BISHOP: "b",
    Piece.BLACK_ROOK: "r",
    Piece.BLACK_QUEEN: "q",
    Piece.BLACK_KING: "k",
}


CHAR_TO_PIECE = {

    value: key
    for key, value in PIECE_TO_CHAR.items()
}


# ==========================================================
# Helpers
# ==========================================================

def is_white(piece: int) -> bool:

    return Piece.WHITE_PAWN <= piece <= Piece.WHITE_KING


def is_black(piece: int) -> bool:

    return Piece.BLACK_PAWN <= piece <= Piece.BLACK_KING


def piece_color(piece: int):

    if is_white(piece):
        return WHITE

    if is_black(piece):
        return BLACK

    return None


def piece_name(piece: int):

    return Piece(piece).name


def is_empty(piece: int):

    return piece == Piece.EMPTY
def is_pawn(piece):
    return (
        piece == Piece.WHITE_PAWN
        or
        piece == Piece.BLACK_PAWN
    )