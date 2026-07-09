from .squares import (
    square_to_string,
    square_from_string,
)
"""
move.py

Packed move representation.

A move is stored inside a single 32-bit integer.

Bit Layout

31                                              0

FFFFFFFF PPPP CCCC MMMM TTTTTT FFFFFF

Bits

0  - 5   : From Square
6  - 11  : To Square
12 - 15  : Moving Piece
16 - 19  : Captured Piece
20 - 23  : Promotion Piece
24 - 31  : Flags
"""

# ==========================================================
# Bit Layout
# ==========================================================

FROM_SHIFT = 0
TO_SHIFT = 6
PIECE_SHIFT = 12
CAPTURE_SHIFT = 16
PROMOTION_SHIFT = 20
FLAGS_SHIFT = 24

# ==========================================================
# Bit Masks
# ==========================================================

SIX_BITS = 0b111111
FOUR_BITS = 0b1111
EIGHT_BITS = 0b11111111

FROM_MASK = SIX_BITS << FROM_SHIFT
TO_MASK = SIX_BITS << TO_SHIFT
PIECE_MASK = FOUR_BITS << PIECE_SHIFT
CAPTURE_MASK = FOUR_BITS << CAPTURE_SHIFT
PROMOTION_MASK = FOUR_BITS << PROMOTION_SHIFT
FLAGS_MASK = EIGHT_BITS << FLAGS_SHIFT

# ==========================================================
# Move Flags
# ==========================================================

QUIET = 0

CAPTURE = 1 << 0

DOUBLE_PAWN_PUSH = 1 << 1

KING_CASTLE = 1 << 2

QUEEN_CASTLE = 1 << 3

EN_PASSANT = 1 << 4

PROMOTION = 1 << 5

CHECK = 1 << 6

CHECKMATE = 1 << 7
# ==========================================================
# Move Encoding
# ==========================================================

def encode_move(
    from_square: int,
    to_square: int,
    moving_piece: int,
    captured_piece: int = 0,
    promotion_piece: int = 0,
    flags: int = QUIET,
) -> int:
    """
    Packs all move information into
    a single 32-bit integer.
    """

    move = 0

    move |= from_square << FROM_SHIFT
    move |= to_square << TO_SHIFT
    move |= moving_piece << PIECE_SHIFT
    move |= captured_piece << CAPTURE_SHIFT
    move |= promotion_piece << PROMOTION_SHIFT
    move |= flags << FLAGS_SHIFT

    return move
# ==========================================================
# Move Decoding
# ==========================================================

def from_square(move: int) -> int:
    """
    Returns the source square.
    """

    return (move & FROM_MASK) >> FROM_SHIFT
def to_square(move: int) -> int:
    """
    Returns the destination square.
    """

    return (move & TO_MASK) >> TO_SHIFT
def moving_piece(move: int) -> int:
    """
    Returns the moving piece.
    """

    return (move & PIECE_MASK) >> PIECE_SHIFT
def captured_piece(move: int) -> int:
    """
    Returns the captured piece.
    """

    return (move & CAPTURE_MASK) >> CAPTURE_SHIFT
def promotion_piece(move: int) -> int:
    """
    Returns the promoted piece.
    """

    return (move & PROMOTION_MASK) >> PROMOTION_SHIFT
def move_flags(move: int) -> int:
    """
    Returns all move flags.
    """

    return (move & FLAGS_MASK) >> FLAGS_SHIFT
# ==========================================================
# Move Predicates
# ==========================================================

def has_flag(move: int, flag: int) -> bool:
    """
    Returns True if the given flag is present.
    """

    return (move_flags(move) & flag) != 0
def is_capture(move: int) -> bool:
    """
    Returns True if this is a capture.
    """

    return has_flag(move, CAPTURE)
def is_promotion(move: int) -> bool:
    """
    Returns True if this move promotes a pawn.
    """

    return has_flag(move, PROMOTION)
def is_double_push(move: int) -> bool:
    """
    Returns True if this is a two-square pawn push.
    """

    return has_flag(move, DOUBLE_PAWN_PUSH)
def is_kingside_castle(move: int) -> bool:
    """
    Returns True if this is kingside castling.
    """

    return has_flag(move, KING_CASTLE)
def is_queenside_castle(move: int) -> bool:
    """
    Returns True if this is queenside castling.
    """

    return has_flag(move, QUEEN_CASTLE)
def is_castle(move: int) -> bool:
    """
    Returns True if this move castles.
    """

    return (
        is_kingside_castle(move)
        or
        is_queenside_castle(move)
    )
def is_en_passant(move: int) -> bool:
    """
    Returns True if this is an en passant capture.
    """

    return has_flag(move, EN_PASSANT)
# def gives_check(move: int) -> bool:
#     """
#     Returns True if the move gives check.
#     """

#     return has_flag(move, CHECK)
# def gives_checkmate(move: int) -> bool:
#     """
#     Returns True if the move gives checkmate.
#     """

#     return has_flag(move, CHECKMATE)
def is_quiet(move: int) -> bool:
    """
    Returns True if the move has no special flags.
    """

    return move_flags(move) == QUIET
# ==========================================================
# String Conversion
# ==========================================================

def move_to_string(move: int) -> str:
    """
    Converts a packed move into UCI notation.

    Examples

    e2e4

    g1f3

    e7e8q
    """

    text = (
        square_to_string(from_square(move))
        +
        square_to_string(to_square(move))
    )

    if is_promotion(move):

        promo = promotion_piece(move)

        if promo in (5, 11):
            text += "q"

        elif promo in (4, 10):
            text += "r"

        elif promo in (3, 9):
            text += "b"

        elif promo in (2, 8):
            text += "n"

    return text
def move_from_string(text: str) -> tuple[int, int]:
    """
    Converts

    e2e4

    into

    (12, 28)
    """

    if len(text) < 4:
        raise ValueError("Invalid move string.")

    frm = square_from_string(text[:2])

    to = square_from_string(text[2:4])

    return frm, to
# ==========================================================
# Validation
# ==========================================================

def validate_move(move: int):
    """
    Performs basic sanity checks.
    """

    frm = from_square(move)
    to = to_square(move)

    if not (0 <= frm < 64):
        raise ValueError("Invalid from square.")

    if not (0 <= to < 64):
        raise ValueError("Invalid to square.")

    piece = moving_piece(move)

    if not (0 <= piece <= 12):
        raise ValueError("Invalid moving piece.")
# ==========================================================
# Debug
# ==========================================================

def print_move(move: int):
    """
    Pretty prints a move.
    """

    print(move_to_string(move))