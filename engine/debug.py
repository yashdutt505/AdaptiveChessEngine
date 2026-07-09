"""
debug.py

Debugging utilities for the chess engine.

This module contains functions for visualizing
the current engine state.

It NEVER modifies the Position.

Its only responsibility is inspection.
"""

from .pieces import *
from .constants import *
from .squares import *
from .bitboard import *
# ==========================================================
# Helpers
# ==========================================================

def _separator(title: str):

    print()

    print("=" * 20)

    print(title)

    print("=" * 20)
def print_side(position):

    print(
        "Side to move :",
        "White"
        if position.side_to_move == WHITE
        else "Black"
    )
def print_castling(position):

    rights = ""

    if position.castling_rights & WHITE_KINGSIDE:
        rights += "K"

    if position.castling_rights & WHITE_QUEENSIDE:
        rights += "Q"

    if position.castling_rights & BLACK_KINGSIDE:
        rights += "k"

    if position.castling_rights & BLACK_QUEENSIDE:
        rights += "q"

    if rights == "":
        rights = "-"

    print("Castling    :", rights)
def print_en_passant(position):

    if position.en_passant == NO_EN_PASSANT:

        ep = "-"

    else:

        ep = square_to_string(
            position.en_passant
        )

    print("En Passant  :", ep)
def print_move_counters(position):

    print(
        "Halfmove    :",
        position.halfmove_clock
    )

    print(
        "Fullmove    :",
        position.fullmove_number
    )
def print_kings(position):

    print(
        "White King  :",
        square_to_string(
            position.white_king_square
        )
    )

    print(
        "Black King  :",
        square_to_string(
            position.black_king_square
        )
    )
def print_hash(position):

    print(

        "Hash        :",

        f"0x{position.hash_key:016X}"

    )
# ==========================================================
# Position Summary
# ==========================================================

def print_position_info(position):

    _separator("POSITION")

    print_side(position)

    print_castling(position)

    print_en_passant(position)

    print_move_counters(position)

    print_kings(position)

    print_hash(position)
# ==========================================================
# Board
# ==========================================================

def print_board(position):
    """
    Prints the current chess board.
    """

    _separator("BOARD")

    position.board.print_board()
# ==========================================================
# Piece Bitboards
# ==========================================================

def print_bitboards(position):
    """
    Prints all 12 piece bitboards.
    """

    _separator("PIECE BITBOARDS")

    position.board.print_bitboards()
# ==========================================================
# Occupancy
# ==========================================================

def print_occupancies(position):
    """
    Prints all occupancy bitboards.
    """

    board = position.board

    _separator("WHITE OCCUPANCY")

    print_bitboard(
        board.white_pieces()
    )

    _separator("BLACK OCCUPANCY")

    print_bitboard(
        board.black_pieces()
    )

    _separator("ALL OCCUPANCY")

    print_bitboard(
        board.occupied_squares()
    )
# ==========================================================
# Piece Counts
# ==========================================================

def print_piece_counts(position):
    """
    Prints the number of each piece.
    """

    board = position.board

    _separator("PIECE COUNTS")

    names = [
        "",
        "White Pawn",
        "White Knight",
        "White Bishop",
        "White Rook",
        "White Queen",
        "White King",
        "Black Pawn",
        "Black Knight",
        "Black Bishop",
        "Black Rook",
        "Black Queen",
        "Black King",
    ]

    for piece in range(
        Piece.WHITE_PAWN,
        Piece.BLACK_KING + 1,
    ):

        count = popcount(
            board.bitboard(piece)
        )

        print(
            f"{names[piece]:15} : {count}"
        )
# ==========================================================
# Material
# ==========================================================

def print_material(position):
    """
    Prints total material count
    for each side.
    """

    board = position.board

    white = 0
    black = 0

    for piece in range(
        Piece.WHITE_PAWN,
        Piece.WHITE_KING + 1,
    ):
        white += popcount(
            board.bitboard(piece)
        )

    for piece in range(
        Piece.BLACK_PAWN,
        Piece.BLACK_KING + 1,
    ):
        black += popcount(
            board.bitboard(piece)
        )

    _separator("MATERIAL")

    print("White Pieces :", white)
    print("Black Pieces :", black)
# ==========================================================
# Complete Debug Dump
# ==========================================================

def debug_position(position):
    """
    Prints every important aspect
    of the current position.
    """

    print_position_info(position)

    print_board(position)

    print_piece_counts(position)

    print_occupancies(position)