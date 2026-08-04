"""Tapered material, piece-placement, pawn, rook, and king evaluation."""

from functools import lru_cache

from .bitboard import bits
from .attacks import DIAGONAL_DIRECTIONS, KNIGHT_ATTACKS, ORTHOGONAL_DIRECTIONS
from .constants import BLACK, WHITE
from .pieces import Piece
from .squares import file_of, rank_of


PIECE_VALUES = {
    Piece.WHITE_PAWN: 100, Piece.BLACK_PAWN: 100,
    Piece.WHITE_KNIGHT: 320, Piece.BLACK_KNIGHT: 320,
    Piece.WHITE_BISHOP: 330, Piece.BLACK_BISHOP: 330,
    Piece.WHITE_ROOK: 500, Piece.BLACK_ROOK: 500,
    Piece.WHITE_QUEEN: 900, Piece.BLACK_QUEEN: 900,
    Piece.WHITE_KING: 0, Piece.BLACK_KING: 0,
}

ENDGAME_VALUES = {
    **PIECE_VALUES,
    Piece.WHITE_KNIGHT: 310, Piece.BLACK_KNIGHT: 310,
    Piece.WHITE_BISHOP: 340, Piece.BLACK_BISHOP: 340,
    Piece.WHITE_ROOK: 520, Piece.BLACK_ROOK: 520,
}

PHASE_WEIGHTS = {1: 0, 2: 1, 3: 1, 4: 2, 5: 4, 6: 0}
MAX_PHASE = 24
FILE_MASKS = tuple(sum(1 << (rank * 8 + file) for rank in range(8)) for file in range(8))


def _kind(piece):
    return (int(piece) - 1) % 6 + 1


def _relative_rank(square, color):
    rank = rank_of(square)
    return rank if color == WHITE else 7 - rank


def _center(square):
    file = file_of(square)
    rank = rank_of(square)
    return int(14 - 4 * (abs(file - 3.5) + abs(rank - 3.5)))


def _placement(piece, square, color):
    kind = _kind(piece)
    relative_rank = _relative_rank(square, color)
    center = _center(square)
    if kind == 1:
        return relative_rank * 6 + center // 3, relative_rank * 10 + center // 4
    if kind == 2:
        return center * 2, center * 2
    if kind == 3:
        return center + relative_rank, center + relative_rank * 2
    if kind == 4:
        seventh = 18 if relative_rank == 6 else 0
        return relative_rank * 2 + seventh, relative_rank * 3 + seventh
    if kind == 5:
        return center // 2, center
    castled = relative_rank == 0 and file_of(square) in (2, 6)
    return (25 if castled else -center), center * 2


def _pawn_features_from_bitboards(pawn_bb, enemy_bb, color):
    pawns = list(bits(pawn_bb))
    enemies = list(bits(enemy_bb))
    files = [file_of(square) for square in pawns]
    score = 0

    for file in set(files):
        score -= max(0, files.count(file) - 1) * 14
    for square in pawns:
        file = file_of(square)
        rank = rank_of(square)
        if not any(abs(other - file) == 1 for other in files):
            score -= 12
        if any(
            abs(file_of(other) - file) == 1
            and abs(rank_of(other) - rank) <= 1
            for other in pawns
            if other != square
        ):
            score += 5
        enemy_ahead = any(
            abs(file_of(other) - file) <= 1
            and (
                rank_of(other) > rank
                if color == WHITE
                else rank_of(other) < rank
            )
            for other in enemies
        )
        if not enemy_ahead:
            advancement = _relative_rank(square, color)
            score += 15 + advancement * advancement * 3
    return score


@lru_cache(maxsize=65_536)
def _pawn_scores(white_pawns, black_pawns):
    return (
        _pawn_features_from_bitboards(white_pawns, black_pawns, WHITE),
        _pawn_features_from_bitboards(black_pawns, white_pawns, BLACK),
    )


def _rook_features(position, color):
    rook = Piece.WHITE_ROOK if color == WHITE else Piece.BLACK_ROOK
    friendly_pawn = Piece.WHITE_PAWN if color == WHITE else Piece.BLACK_PAWN
    enemy_pawn = Piece.BLACK_PAWN if color == WHITE else Piece.WHITE_PAWN
    score = 0
    board = position.board
    friendly_pawns = board.bitboard(friendly_pawn)
    enemy_pawns = board.bitboard(enemy_pawn)
    for square in bits(board.bitboard(rook)):
        file = file_of(square)
        friendly_on_file = friendly_pawns & FILE_MASKS[file]
        enemy_on_file = enemy_pawns & FILE_MASKS[file]
        if not friendly_on_file:
            score += 12
            if not enemy_on_file:
                score += 10
    return score


def _king_safety(position, color):
    king_square = position.king_square(color)
    pawn = Piece.WHITE_PAWN if color == WHITE else Piece.BLACK_PAWN
    direction = 1 if color == WHITE else -1
    king_file = file_of(king_square)
    king_rank = rank_of(king_square)
    score = 0
    for df in (-1, 0, 1):
        file = king_file + df
        if not 0 <= file < 8:
            continue
        shielded = False
        for distance in (1, 2):
            rank = king_rank + direction * distance
            if 0 <= rank < 8 and position.piece_at(rank * 8 + file) == pawn:
                score += 12 if distance == 1 else 6
                shielded = True
                break
        if not shielded:
            score -= 10
    return score


def _slider_mobility(position, square, color, directions):
    friendly = position.board.white_occ if color == WHITE else position.board.black_occ
    source_file = file_of(square)
    source_rank = rank_of(square)
    mobility = 0
    for df, dr in directions:
        file = source_file + df
        rank = source_rank + dr
        while 0 <= file < 8 and 0 <= rank < 8:
            target = rank * 8 + file
            mask = 1 << target
            if friendly & mask:
                break
            mobility += 1
            if position.board.all_occ & mask:
                break
            file += df
            rank += dr
    return mobility


def _mobility(position, color):
    board = position.board
    friendly = board.white_occ if color == WHITE else board.black_occ
    knight = Piece.WHITE_KNIGHT if color == WHITE else Piece.BLACK_KNIGHT
    bishop = Piece.WHITE_BISHOP if color == WHITE else Piece.BLACK_BISHOP
    rook = Piece.WHITE_ROOK if color == WHITE else Piece.BLACK_ROOK
    queen = Piece.WHITE_QUEEN if color == WHITE else Piece.BLACK_QUEEN
    score = sum((KNIGHT_ATTACKS[square] & ~friendly).bit_count() * 4 for square in bits(board.bitboard(knight)))
    score += sum(_slider_mobility(position, square, color, DIAGONAL_DIRECTIONS) * 3 for square in bits(board.bitboard(bishop)))
    score += sum(_slider_mobility(position, square, color, ORTHOGONAL_DIRECTIONS) * 2 for square in bits(board.bitboard(rook)))
    score += sum(
        _slider_mobility(position, square, color, DIAGONAL_DIRECTIONS + ORTHOGONAL_DIRECTIONS)
        for square in bits(board.bitboard(queen))
    )
    return score


def _finish_evaluation(position, mg, eg, bishops, phase):
    board = position.board
    pawn_scores = _pawn_scores(
        board.bitboard(Piece.WHITE_PAWN),
        board.bitboard(Piece.BLACK_PAWN),
    )
    for color in (WHITE, BLACK):
        structure = pawn_scores[color]
        rooks = _rook_features(position, color)
        bishop_pair = 30 if bishops[color] >= 2 else 0
        mobility = _mobility(position, color)
        mg[color] += structure + rooks + bishop_pair + mobility + _king_safety(position, color)
        eg[color] += structure + rooks + bishop_pair + mobility // 2

    phase = min(phase, MAX_PHASE)
    mg_score = mg[WHITE] - mg[BLACK]
    eg_score = eg[WHITE] - eg[BLACK]
    score = (mg_score * phase + eg_score * (MAX_PHASE - phase)) // MAX_PHASE
    return score if position.side_to_move == WHITE else -score


def evaluate_reference(position):
    """Fully recompute evaluation; used as an incremental-state oracle."""
    mg = [0, 0]
    eg = [0, 0]
    bishops = [0, 0]
    phase = 0

    board = position.board
    for piece in range(Piece.WHITE_PAWN, Piece.BLACK_KING + 1):
        color = WHITE if piece <= Piece.WHITE_KING else BLACK
        kind = _kind(piece)
        piece_bb = board.bitboard(piece)
        count = piece_bb.bit_count()
        phase += PHASE_WEIGHTS[kind] * count
        if kind == 3:
            bishops[color] += count
        for square in bits(piece_bb):
            mg_place, eg_place = PLACEMENT[piece][square]
            mg[color] += PIECE_VALUES[piece] + mg_place
            eg[color] += ENDGAME_VALUES[piece] + eg_place

    return _finish_evaluation(position, mg, eg, bishops, phase)


def evaluate(position):
    """Return tapered evaluation using incrementally maintained base scores."""
    return _finish_evaluation(
        position,
        position.mg_base.copy(),
        position.eg_base.copy(),
        position.bishop_counts,
        position.phase,
    )


PLACEMENT = tuple(
    tuple(
        _placement(piece, square, WHITE if piece <= Piece.WHITE_KING else BLACK)
        if piece != Piece.EMPTY else (0, 0)
        for square in range(64)
    )
    for piece in range(13)
)
