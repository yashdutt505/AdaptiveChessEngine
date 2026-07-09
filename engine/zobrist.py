"""
zobrist.py

Zobrist hashing utilities.

A Zobrist hash uniquely identifies a chess position.

The hash consists of XOR'ing random 64-bit numbers
representing:

- Piece placement
- Side to move
- Castling rights
- En passant file
"""

import random

from .pieces import Piece
from .constants import *
# ==========================================================
# Random Generator
# ==========================================================

_RANDOM = random.Random(0)
# ==========================================================
# Zobrist Tables
# ==========================================================

PIECE_KEYS = [
    [0 for _ in range(64)]
    for _ in range(13)
]

CASTLING_KEYS = [0] * 16

EP_KEYS = [0] * 8

SIDE_KEY = 0
# ==========================================================
# Initialization
# ==========================================================

def _random_u64():

    return _RANDOM.getrandbits(64)


def initialize_zobrist():
    """
    Generates all random numbers.
    """

    global SIDE_KEY

    for piece in range(13):

        for square in range(64):

            PIECE_KEYS[piece][square] = _random_u64()

    for rights in range(16):

        CASTLING_KEYS[rights] = _random_u64()

    for file in range(8):

        EP_KEYS[file] = _random_u64()

    SIDE_KEY = _random_u64()
# ==========================================================
# Hash Helpers
# ==========================================================

def piece_hash(piece: int, square: int) -> int:
    """
    Returns the Zobrist key for a piece on a square.
    """

    return PIECE_KEYS[piece][square]


def castling_hash(rights: int) -> int:
    """
    Returns the Zobrist key for castling rights.
    """

    return CASTLING_KEYS[rights]


def en_passant_hash(square: int) -> int:
    """
    Returns the Zobrist key for the en passant file.

    Only the file matters.
    """

    if square == NO_EN_PASSANT:
        return 0

    file = square % 8

    return EP_KEYS[file]


def side_hash() -> int:
    """
    Returns the side-to-move key.
    """

    return SIDE_KEY
# ==========================================================
# Full Hash Computation
# ==========================================================

def compute_hash(position) -> int:
    """
    Computes the complete Zobrist hash
    from scratch.
    """

    key = 0

    # -----------------------------------------
    # Pieces
    # -----------------------------------------

    for square in range(64):

        piece = position.board.piece_at(square)

        if piece != Piece.EMPTY:

            key ^= PIECE_KEYS[piece][square]

    # -----------------------------------------
    # Side to move
    # -----------------------------------------

    if position.side_to_move == BLACK:

        key ^= SIDE_KEY

    # -----------------------------------------
    # Castling rights
    # -----------------------------------------

    key ^= CASTLING_KEYS[
        position.castling_rights
    ]

    # -----------------------------------------
    # En Passant
    # -----------------------------------------

    if position.en_passant != NO_EN_PASSANT:

        key ^= EP_KEYS[
            position.en_passant % 8
        ]

    return key
# ==========================================================
# Validation
# ==========================================================

def verify_hash(position) -> bool:
    """
    Verifies that the stored hash matches
    a recomputed hash.
    """

    return (
        position.hash_key
        ==
        compute_hash(position)
    )


def update_position_hash(position):
    """
    Recomputes and stores the hash.
    """

    position.hash_key = compute_hash(position)
# ==========================================================
# Debug
# ==========================================================

def print_hash(position):
    """
    Prints the current position hash.
    """

    print(
        f"0x{position.hash_key:016X}"
    )