"""Static exchange evaluation for capture ordering and pruning."""

from .attacks import DIAGONAL_DIRECTIONS, KING_ATTACKS, KNIGHT_ATTACKS, ORTHOGONAL_DIRECTIONS
from .constants import BLACK, WHITE
from .evaluation import PIECE_VALUES
from .move import captured_piece, from_square, is_en_passant, is_promotion, moving_piece, promotion_piece, to_square
from .pieces import Piece
from .squares import file_of, make_square, rank_of


KIND_ORDER = (1, 2, 3, 4, 5, 6)


def _piece_for(color, kind):
    return Piece(kind if color == WHITE else kind + 6)


def _piece_on(pieces, square):
    mask = 1 << square
    for piece in range(Piece.WHITE_PAWN, Piece.BLACK_KING + 1):
        if pieces[piece] & mask:
            return piece
    return Piece.EMPTY


def _attackers_to(square, color, pieces, occupied):
    attackers = 0
    target_file = file_of(square)
    target_rank = rank_of(square)

    pawn = _piece_for(color, 1)
    source_rank = target_rank - 1 if color == WHITE else target_rank + 1
    if 0 <= source_rank < 8:
        for source_file in (target_file - 1, target_file + 1):
            if 0 <= source_file < 8:
                source = make_square(source_file, source_rank)
                if pieces[pawn] & (1 << source):
                    attackers |= 1 << source

    attackers |= KNIGHT_ATTACKS[square] & pieces[_piece_for(color, 2)]
    attackers |= KING_ATTACKS[square] & pieces[_piece_for(color, 6)]

    bishop = _piece_for(color, 3)
    rook = _piece_for(color, 4)
    queen = _piece_for(color, 5)
    for directions, sliders in (
        (DIAGONAL_DIRECTIONS, (bishop, queen)),
        (ORTHOGONAL_DIRECTIONS, (rook, queen)),
    ):
        for df, dr in directions:
            file = target_file + df
            rank = target_rank + dr
            while 0 <= file < 8 and 0 <= rank < 8:
                source = make_square(file, rank)
                mask = 1 << source
                if occupied & mask:
                    if any(pieces[piece] & mask for piece in sliders):
                        attackers |= mask
                    break
                file += df
                rank += dr
    return attackers


def _least_attacker(square, color, pieces, occupied):
    attackers = _attackers_to(square, color, pieces, occupied)
    for kind in KIND_ORDER:
        piece = _piece_for(color, kind)
        candidates = attackers & pieces[piece]
        if candidates:
            source = (candidates & -candidates).bit_length() - 1
            return source, piece
    return None


def _recapture_gain(square, color, occupant, pieces, occupied):
    attacker = _least_attacker(square, color, pieces, occupied)
    if attacker is None:
        return 0
    source, piece = attacker
    next_pieces = pieces.copy()
    source_mask = 1 << source
    target_mask = 1 << square
    next_pieces[piece] &= ~source_mask
    next_pieces[occupant] &= ~target_mask
    next_pieces[piece] |= target_mask
    next_occupied = (occupied & ~source_mask) | target_mask
    gain = PIECE_VALUES[occupant] - _recapture_gain(
        square, color ^ 1, piece, next_pieces, next_occupied
    )
    return max(0, gain)


def static_exchange_eval(position, move):
    """Return the material result of optimal exchanges on the move target."""
    captured = captured_piece(move)
    if captured == Piece.EMPTY:
        return 0

    board = position.board
    pieces = board.bitboards.copy()
    occupied = board.all_occ
    frm = from_square(move)
    to = to_square(move)
    mover = moving_piece(move)
    placed = promotion_piece(move) if is_promotion(move) else mover
    frm_mask = 1 << frm
    to_mask = 1 << to
    capture_square = to
    if is_en_passant(move):
        capture_square = to - 8 if position.side_to_move == WHITE else to + 8
    capture_mask = 1 << capture_square

    pieces[mover] &= ~frm_mask
    pieces[captured] &= ~capture_mask
    pieces[placed] |= to_mask
    occupied &= ~frm_mask
    occupied &= ~capture_mask
    occupied |= to_mask

    promotion_gain = PIECE_VALUES[placed] - PIECE_VALUES[mover]
    return PIECE_VALUES[captured] + promotion_gain - _recapture_gain(
        to, position.side_to_move ^ 1, placed, pieces, occupied
    )
