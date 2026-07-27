"""Deterministic static chess position evaluation."""

from .constants import BLACK, WHITE
from .pieces import Piece, is_black, is_white
from .squares import file_of, rank_of


PIECE_VALUES = {
    Piece.WHITE_PAWN: 100,
    Piece.WHITE_KNIGHT: 320,
    Piece.WHITE_BISHOP: 330,
    Piece.WHITE_ROOK: 500,
    Piece.WHITE_QUEEN: 900,
    Piece.WHITE_KING: 0,
    Piece.BLACK_PAWN: 100,
    Piece.BLACK_KNIGHT: 320,
    Piece.BLACK_BISHOP: 330,
    Piece.BLACK_ROOK: 500,
    Piece.BLACK_QUEEN: 900,
    Piece.BLACK_KING: 0,
}


def _relative_rank(square, color):
    rank = rank_of(square)
    return rank if color == WHITE else 7 - rank


def _center_bonus(square):
    file = file_of(square)
    rank = rank_of(square)
    return int(14 - 4 * (abs(file - 3.5) + abs(rank - 3.5)))


def _piece_square(piece, square, color, endgame):
    center = _center_bonus(square)
    relative_rank = _relative_rank(square, color)
    kind = (int(piece) - 1) % 6
    if kind == 0:  # pawn
        return relative_rank * 7 + center // 3
    if kind == 1:  # knight
        return center * 2
    if kind == 2:  # bishop
        return center
    if kind == 3:  # rook
        return relative_rank * 2
    if kind == 4:  # queen
        return center // 2
    return center * 2 if endgame else -center


def _pawn_structure(position, color):
    pawn = Piece.WHITE_PAWN if color == WHITE else Piece.BLACK_PAWN
    enemy_pawn = Piece.BLACK_PAWN if color == WHITE else Piece.WHITE_PAWN
    pawns = [sq for sq in range(64) if position.piece_at(sq) == pawn]
    enemies = [sq for sq in range(64) if position.piece_at(sq) == enemy_pawn]
    files = [file_of(sq) for sq in pawns]
    score = 0

    for square in pawns:
        file = file_of(square)
        rank = rank_of(square)
        if files.count(file) > 1:
            score -= 12
        if not any(abs(other_file - file) == 1 for other_file in files):
            score -= 10
        ahead = (
            lambda enemy_rank: enemy_rank > rank
            if color == WHITE
            else enemy_rank < rank
        )
        if not any(
            abs(file_of(enemy) - file) <= 1 and ahead(rank_of(enemy))
            for enemy in enemies
        ):
            score += 12 + 6 * _relative_rank(square, color)
    return score


def evaluate(position):
    """Return a centipawn score from the side-to-move perspective."""
    non_pawn_material = 0
    for square in range(64):
        piece = position.piece_at(square)
        if piece not in (Piece.EMPTY, Piece.WHITE_PAWN, Piece.BLACK_PAWN):
            non_pawn_material += PIECE_VALUES[piece]
    endgame = non_pawn_material <= 2600

    white = 0
    black = 0
    white_bishops = 0
    black_bishops = 0
    for square in range(64):
        piece = position.piece_at(square)
        if piece == Piece.EMPTY:
            continue
        color = WHITE if is_white(piece) else BLACK
        value = PIECE_VALUES[piece] + _piece_square(piece, square, color, endgame)
        if is_white(piece):
            white += value
            white_bishops += piece == Piece.WHITE_BISHOP
        elif is_black(piece):
            black += value
            black_bishops += piece == Piece.BLACK_BISHOP

    white += _pawn_structure(position, WHITE) + (30 if white_bishops >= 2 else 0)
    black += _pawn_structure(position, BLACK) + (30 if black_bishops >= 2 else 0)
    score = white - black
    return score if position.side_to_move == WHITE else -score
