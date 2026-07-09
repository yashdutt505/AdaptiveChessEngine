"""
validator.py

Validation utilities.

These functions verify that a Position object
is internally consistent.

They DO NOT check move legality.

They only verify that the engine's internal
representation is correct.
"""

from .pieces import *
from .constants import *
from .bitboard import *
from .squares import *
from .zobrist import compute_hash
class ValidationError(Exception):
    """
    Raised when a Position fails validation.
    """
    pass
def _count_piece(position, piece):
    """
    Counts a given piece on the board.
    """

    count = 0

    for sq in range(64):

        if position.board.piece_at(sq) == piece:

            count += 1

    return count
def validate_side(position):

    if position.side_to_move not in (
        WHITE,
        BLACK,
    ):

        raise ValidationError(
            "Invalid side to move."
        )
def validate_kings(position):

    white = _count_piece(
        position,
        Piece.WHITE_KING,
    )

    black = _count_piece(
        position,
        Piece.BLACK_KING,
    )

    if white != 1:

        raise ValidationError(
            f"Expected exactly one white king, found {white}."
        )

    if black != 1:

        raise ValidationError(
            f"Expected exactly one black king, found {black}."
        )
def validate_king_cache(position):

    if (
        position.board.piece_at(
            position.white_king_square
        )
        != Piece.WHITE_KING
    ):

        raise ValidationError(
            "White king cache incorrect."
        )

    if (
        position.board.piece_at(
            position.black_king_square
        )
        != Piece.BLACK_KING
    ):

        raise ValidationError(
            "Black king cache incorrect."
        )
# ==========================================================
# Board Consistency
# ==========================================================

def validate_bitboards(position):
    """
    Ensures every piece bitboard matches
    the mailbox board.
    """

    board = position.board

    expected = [0] * 13

    for square in range(64):

        piece = board.piece_at(square)

        if piece != Piece.EMPTY:

            expected[piece] = set_bit(
                expected[piece],
                square,
            )

    for piece in range(
        Piece.WHITE_PAWN,
        Piece.BLACK_KING + 1,
    ):

        if expected[piece] != board.bitboard(piece):

            raise ValidationError(
                f"Bitboard mismatch for piece {piece}."
            )
# ==========================================================
# Occupancy Validation
# ==========================================================

def validate_occupancy(position):
    """
    Verifies occupancy bitboards.
    """

    board = position.board

    white = EMPTY_BOARD
    black = EMPTY_BOARD

    for piece in range(
        Piece.WHITE_PAWN,
        Piece.WHITE_KING + 1,
    ):

        white |= board.bitboard(piece)

    for piece in range(
        Piece.BLACK_PAWN,
        Piece.BLACK_KING + 1,
    ):

        black |= board.bitboard(piece)

    if white != board.white_pieces():

        raise ValidationError(
            "White occupancy incorrect."
        )

    if black != board.black_pieces():

        raise ValidationError(
            "Black occupancy incorrect."
        )

    if (white | black) != board.occupied_squares():

        raise ValidationError(
            "Combined occupancy incorrect."
        )
# ==========================================================
# Castling Validation
# ==========================================================

def validate_castling(position):
    """
    Validates castling rights flags.
    """

    rights = position.castling_rights

    if rights < 0 or rights > ALL_CASTLING_RIGHTS:

        raise ValidationError(
            "Invalid castling rights."
        )
# ==========================================================
# En Passant Validation
# ==========================================================

def validate_en_passant(position):
    """
    Validates the en passant square.
    """

    ep = position.en_passant

    if ep == NO_EN_PASSANT:
        return

    if not valid_square(ep):

        raise ValidationError(
            "Invalid en passant square."
        )
# ==========================================================
# Hash Validation
# ==========================================================

def validate_hash(position):
    """
    Verifies that the stored Zobrist hash
    matches a freshly computed hash.
    """

    expected = compute_hash(position)

    if expected != position.hash_key:

        raise ValidationError(
            "Zobrist hash mismatch."
        )
# ==========================================================
# Move Counter Validation
# ==========================================================

def validate_move_counters(position):
    """
    Validates the move counters.
    """

    if position.halfmove_clock < 0:

        raise ValidationError(
            "Halfmove clock cannot be negative."
        )

    if position.fullmove_number <= 0:

        raise ValidationError(
            "Fullmove number must be positive."
        )
# ==========================================================
# Board Validation
# ==========================================================

def validate_board(position):
    """
    Runs every board-related validation.
    """

    validate_kings(position)

    validate_king_cache(position)

    validate_bitboards(position)

    validate_occupancy(position)
# ==========================================================
# Position Validation
# ==========================================================

def validate_position(position):
    """
    Runs every validation check.

    Raises ValidationError if any
    invariant is broken.
    """

    validate_side(position)

    validate_board(position)

    validate_castling(position)

    validate_en_passant(position)

    validate_move_counters(position)

    validate_hash(position)

    return True
# ==========================================================
# Convenience
# ==========================================================

def is_valid(position):
    """
    Returns True if the position is valid.
    """

    try:

        validate_position(position)

        return True

    except ValidationError:

        return False
def assert_valid(position):
    """
    Convenience wrapper used during development.
    """

    validate_position(position)
