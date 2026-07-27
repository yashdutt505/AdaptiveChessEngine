"""Attack detection used by legal move generation."""

from .constants import BLACK, WHITE
from .pieces import Piece
from .squares import file_of, make_square, rank_of


KNIGHT_DELTAS = (
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
)
KING_DELTAS = (
    (-1, -1), (-1, 0), (-1, 1), (0, -1),
    (0, 1), (1, -1), (1, 0), (1, 1),
)
DIAGONAL_DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ORTHOGONAL_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _piece_for(color, white_piece, black_piece):
    return white_piece if color == WHITE else black_piece


def is_square_attacked(position, square, by_color):
    """Return whether ``square`` is attacked by ``by_color``."""
    board = position.board
    target_file = file_of(square)
    target_rank = rank_of(square)

    pawn = _piece_for(by_color, Piece.WHITE_PAWN, Piece.BLACK_PAWN)
    source_rank = target_rank - 1 if by_color == WHITE else target_rank + 1
    if 0 <= source_rank < 8:
        for source_file in (target_file - 1, target_file + 1):
            if 0 <= source_file < 8:
                if board.piece_at(make_square(source_file, source_rank)) == pawn:
                    return True

    knight = _piece_for(by_color, Piece.WHITE_KNIGHT, Piece.BLACK_KNIGHT)
    for df, dr in KNIGHT_DELTAS:
        file = target_file + df
        rank = target_rank + dr
        if 0 <= file < 8 and 0 <= rank < 8:
            if board.piece_at(make_square(file, rank)) == knight:
                return True

    king = _piece_for(by_color, Piece.WHITE_KING, Piece.BLACK_KING)
    for df, dr in KING_DELTAS:
        file = target_file + df
        rank = target_rank + dr
        if 0 <= file < 8 and 0 <= rank < 8:
            if board.piece_at(make_square(file, rank)) == king:
                return True

    bishop = _piece_for(by_color, Piece.WHITE_BISHOP, Piece.BLACK_BISHOP)
    rook = _piece_for(by_color, Piece.WHITE_ROOK, Piece.BLACK_ROOK)
    queen = _piece_for(by_color, Piece.WHITE_QUEEN, Piece.BLACK_QUEEN)

    for directions, attackers in (
        (DIAGONAL_DIRECTIONS, (bishop, queen)),
        (ORTHOGONAL_DIRECTIONS, (rook, queen)),
    ):
        for df, dr in directions:
            file = target_file + df
            rank = target_rank + dr
            while 0 <= file < 8 and 0 <= rank < 8:
                piece = board.piece_at(make_square(file, rank))
                if piece != Piece.EMPTY:
                    if piece in attackers:
                        return True
                    break
                file += df
                rank += dr

    return False


def is_in_check(position, color=None):
    """Return whether the requested side's king is in check."""
    color = position.side_to_move if color is None else color
    king_square = position.king_square(color)
    if king_square < 0:
        raise ValueError("Position has no king for the requested color")
    return is_square_attacked(position, king_square, color ^ 1)
