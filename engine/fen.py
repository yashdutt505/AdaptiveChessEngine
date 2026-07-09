"""
fen.py

FEN parser and serializer.

Responsibilities:

- Load a FEN into Position
- Export Position to FEN
- Validate FEN fields
- Keep parsing logic isolated
"""

from .pieces import *
from .position import Position
from .constants import *
from .squares import *
from .zobrist import compute_hash
# ==========================================================
# Internal Helpers
# ==========================================================

def _parse_side(field: str) -> int:

    if field == "w":
        return WHITE

    if field == "b":
        return BLACK

    raise ValueError(f"Invalid side to move: {field}")
def _parse_castling(field: str) -> int:

    if field == "-":
        return 0

    rights = 0

    valid = set("KQkq")

    for c in field:

        if c not in valid:
            raise ValueError(
                f"Invalid castling character: {c}"
            )

        if c == "K":
            rights |= WHITE_KINGSIDE

        elif c == "Q":
            rights |= WHITE_QUEENSIDE

        elif c == "k":
            rights |= BLACK_KINGSIDE

        elif c == "q":
            rights |= BLACK_QUEENSIDE

    return rights
def _parse_en_passant(field: str):

    if field == "-":
        return NO_EN_PASSANT

    return square_from_string(field)
def _parse_move_numbers(
    halfmove: str,
    fullmove: str
):

    try:

        half = int(halfmove)

        full = int(fullmove)

    except ValueError:

        raise ValueError(
            "Halfmove/fullmove must be integers."
        )

    if half < 0:
        raise ValueError(
            "Halfmove clock cannot be negative."
        )

    if full <= 0:
        raise ValueError(
            "Fullmove number must be >= 1."
        )

    return half, full
def _load_board(position: Position, board: str):

    rank = 7

    file = 0

    for c in board:

        if c == "/":

            if file != 8:
                raise ValueError(
                    "Invalid FEN rank."
                )

            rank -= 1

            file = 0

            continue

        if c.isdigit():

            file += int(c)

            if file > 8:
                raise ValueError(
                    "Too many squares in rank."
                )

            continue

        if c not in CHAR_TO_PIECE:

            raise ValueError(
                f"Unknown piece: {c}"
            )

        square = make_square(file, rank)

        piece = CHAR_TO_PIECE[c]

        position.add_piece(square, piece)

        file += 1

    if rank != 0 or file != 8:
        raise ValueError(
            "Board description incomplete."
        )
    
def load_fen(
    position: Position,
    fen: str
):

    fields = fen.strip().split()

    if len(fields) != 6:
        raise ValueError(
            "FEN must contain six fields."
        )

    board_field = fields[0]
    side_field = fields[1]
    castle_field = fields[2]
    ep_field = fields[3]
    half_field = fields[4]
    full_field = fields[5]

    # ------------------------------------
    # Reset
    # ------------------------------------

    position.clear()

    # ------------------------------------
    # Load Board
    # ------------------------------------

    _load_board(
        position,
        board_field
    )

    # ------------------------------------
    # Remaining State
    # ------------------------------------

    position.side_to_move = _parse_side(
        side_field
    )

    position.castling_rights = _parse_castling(
        castle_field
    )

    position.en_passant = _parse_en_passant(
        ep_field
    )

    (
        position.halfmove_clock,
        position.fullmove_number,
    ) = _parse_move_numbers(
        half_field,
        full_field,
    )
    position.hash_key = compute_hash(position)
# ==========================================================
# Export Helpers
# ==========================================================

def _board_to_fen(position: Position) -> str:
    """
    Converts the board into the first FEN field.
    """

    parts = []

    for rank in range(7, -1, -1):

        empty = 0

        for file in range(8):

            square = make_square(file, rank)

            piece = position.board.piece_at(square)

            if piece == Piece.EMPTY:

                empty += 1

            else:

                if empty:

                    parts.append(str(empty))

                    empty = 0

                parts.append(
                    PIECE_TO_CHAR[piece]
                )

        if empty:
            parts.append(str(empty))

        if rank:
            parts.append("/")

    return "".join(parts)
def _castling_to_string(rights: int) -> str:

    result = ""

    if rights & WHITE_KINGSIDE:
        result += "K"

    if rights & WHITE_QUEENSIDE:
        result += "Q"

    if rights & BLACK_KINGSIDE:
        result += "k"

    if rights & BLACK_QUEENSIDE:
        result += "q"

    return result if result else "-"
# ==========================================================
# Export Position
# ==========================================================

def position_to_fen(
    position: Position
) -> str:

    board = _board_to_fen(position)

    side = (
        "w"
        if position.side_to_move == WHITE
        else "b"
    )

    castle = _castling_to_string(
        position.castling_rights
    )

    ep = square_to_string(
        position.en_passant
    )

    return (
        f"{board} "
        f"{side} "
        f"{castle} "
        f"{ep} "
        f"{position.halfmove_clock} "
        f"{position.fullmove_number}"
    )
# ==========================================================
# Verification
# ==========================================================

def verify_round_trip(fen: str):

    position = Position()

    load_fen(position, fen)

    exported = position_to_fen(position)

    if exported != fen:

        raise AssertionError(
            "\n"
            f"Original : {fen}\n"
            f"Exported : {exported}"
        )

    return True
def load_start_position(
    position: Position
):

    load_fen(
        position,
        START_FEN
    )