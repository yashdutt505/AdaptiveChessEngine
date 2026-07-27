"""Terminal game-state and draw detection."""

from .bitboard import popcount
from .pieces import Piece
from .squares import file_of, rank_of


def is_fifty_move_draw(position):
    return position.halfmove_clock >= 100


def repetition_count(position):
    """Count occurrences of the current hash in the reversible history."""
    count = 1
    reversible = (
        position.history.stack[-position.halfmove_clock :]
        if position.halfmove_clock
        else ()
    )
    count += sum(undo.hash_key == position.hash_key for undo in reversible)
    return count


def is_threefold_repetition(position):
    return repetition_count(position) >= 3


def is_insufficient_material(position):
    """Recognize standard positions where mate is impossible."""
    board = position.board
    for piece in (
        Piece.WHITE_PAWN,
        Piece.BLACK_PAWN,
        Piece.WHITE_ROOK,
        Piece.BLACK_ROOK,
        Piece.WHITE_QUEEN,
        Piece.BLACK_QUEEN,
    ):
        if board.bitboard(piece):
            return False

    white_knights = popcount(board.bitboard(Piece.WHITE_KNIGHT))
    black_knights = popcount(board.bitboard(Piece.BLACK_KNIGHT))
    white_bishops = list(_squares(board.bitboard(Piece.WHITE_BISHOP)))
    black_bishops = list(_squares(board.bitboard(Piece.BLACK_BISHOP)))
    minors = white_knights + black_knights + len(white_bishops) + len(black_bishops)

    if minors <= 1:
        return True
    if white_knights == 0 and black_knights == 0:
        bishop_colors = {
            (file_of(square) + rank_of(square)) % 2
            for square in white_bishops + black_bishops
        }
        return len(bishop_colors) <= 1
    return False


def is_rule_draw(position):
    return (
        is_fifty_move_draw(position)
        or is_threefold_repetition(position)
        or is_insufficient_material(position)
    )


def _squares(bitboard):
    while bitboard:
        square = (bitboard & -bitboard).bit_length() - 1
        yield square
        bitboard &= bitboard - 1
