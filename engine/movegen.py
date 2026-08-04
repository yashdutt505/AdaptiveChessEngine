"""Pseudo-legal and fully legal chess move generation."""

from .attacks import (
    DIAGONAL_DIRECTIONS,
    ORTHOGONAL_DIRECTIONS,
    KING_ATTACKS,
    KNIGHT_ATTACKS,
    is_in_check,
    is_square_attacked,
)
from .constants import (
    BLACK,
    BLACK_KINGSIDE,
    BLACK_QUEENSIDE,
    NO_EN_PASSANT,
    WHITE,
    WHITE_KINGSIDE,
    WHITE_QUEENSIDE,
)
from .bitboard import bits
from .move import (
    CAPTURE,
    DOUBLE_PAWN_PUSH,
    EN_PASSANT,
    KING_CASTLE,
    PROMOTION,
    QUEEN_CASTLE,
    encode_move,
    from_square,
    is_capture,
    is_en_passant,
    is_promotion,
    moving_piece,
    to_square,
)
from .pieces import Piece, is_black, is_white
from .squares import (
    A1, A8, B1, B8, C1, C8, D1, D8, E1, E8,
    F1, F8, G1, G8, H1, H8, file_of, make_square, rank_of,
)


def _friendly(piece, color):
    return is_white(piece) if color == WHITE else is_black(piece)


def _enemy(piece, color):
    return is_black(piece) if color == WHITE else is_white(piece)


def _add_move(moves, position, frm, to, piece, extra_flags=0, promotion=Piece.EMPTY):
    captured = position.piece_at(to)
    flags = extra_flags | (CAPTURE if captured != Piece.EMPTY else 0)
    moves.append(encode_move(frm, to, piece, captured, promotion, flags))


def _generate_pawns(position, moves, color, tactical_only=False):
    board = position.board
    pawn = Piece.WHITE_PAWN if color == WHITE else Piece.BLACK_PAWN
    enemy_pawn = Piece.BLACK_PAWN if color == WHITE else Piece.WHITE_PAWN
    promotions = (
        (Piece.WHITE_QUEEN, Piece.WHITE_ROOK, Piece.WHITE_BISHOP, Piece.WHITE_KNIGHT)
        if color == WHITE
        else (Piece.BLACK_QUEEN, Piece.BLACK_ROOK, Piece.BLACK_BISHOP, Piece.BLACK_KNIGHT)
    )
    direction = 1 if color == WHITE else -1
    start_rank = 1 if color == WHITE else 6
    promotion_rank = 7 if color == WHITE else 0

    for frm in bits(board.bitboard(pawn)):
        file = file_of(frm)
        rank = rank_of(frm)
        next_rank = rank + direction

        if 0 <= next_rank < 8:
            to = make_square(file, next_rank)
            if board.empty(to):
                if next_rank == promotion_rank:
                    for promoted in promotions:
                        moves.append(encode_move(frm, to, pawn, promotion_piece=promoted, flags=PROMOTION))
                elif not tactical_only:
                    moves.append(encode_move(frm, to, pawn))
                    if rank == start_rank:
                        double_to = make_square(file, rank + 2 * direction)
                        if board.empty(double_to):
                            moves.append(encode_move(frm, double_to, pawn, flags=DOUBLE_PAWN_PUSH))

            for capture_file in (file - 1, file + 1):
                if not 0 <= capture_file < 8:
                    continue
                capture_to = make_square(capture_file, next_rank)
                target = board.piece_at(capture_to)
                if _enemy(target, color) and target not in (Piece.WHITE_KING, Piece.BLACK_KING):
                    if next_rank == promotion_rank:
                        for promoted in promotions:
                            moves.append(
                                encode_move(
                                    frm, capture_to, pawn, target, promoted,
                                    CAPTURE | PROMOTION,
                                )
                            )
                    else:
                        moves.append(encode_move(frm, capture_to, pawn, target, flags=CAPTURE))
                elif capture_to == position.en_passant and position.en_passant != NO_EN_PASSANT:
                    captured_square = capture_to - 8 if color == WHITE else capture_to + 8
                    if board.piece_at(captured_square) == enemy_pawn:
                        moves.append(
                            encode_move(
                                frm, capture_to, pawn, enemy_pawn,
                                flags=CAPTURE | EN_PASSANT,
                            )
                        )


def _generate_leaper(position, moves, color, piece, attack_table, tactical_only=False):
    friendly = position.board.white_occ if color == WHITE else position.board.black_occ
    kings = position.board.bitboard(Piece.WHITE_KING) | position.board.bitboard(Piece.BLACK_KING)
    for frm in bits(position.board.bitboard(piece)):
        targets = attack_table[frm] & ~friendly & ~kings
        if tactical_only:
            enemy = position.board.black_occ if color == WHITE else position.board.white_occ
            targets &= enemy
        for to in bits(targets):
            target = position.piece_at(to)
            _add_move(moves, position, frm, to, piece)


def _generate_slider(position, moves, color, pieces, directions, tactical_only=False):
    sliders = 0
    for piece in pieces:
        sliders |= position.board.bitboard(piece)
    for frm in bits(sliders):
        piece = position.piece_at(frm)
        frm_file = file_of(frm)
        frm_rank = rank_of(frm)
        if tactical_only:
            for df, dr in directions:
                file = frm_file + df
                rank = frm_rank + dr
                while 0 <= file < 8 and 0 <= rank < 8:
                    to = make_square(file, rank)
                    target = position.piece_at(to)
                    if target != Piece.EMPTY:
                        if _enemy(target, color) and target not in (
                            Piece.WHITE_KING, Piece.BLACK_KING
                        ):
                            _add_move(moves, position, frm, to, piece)
                        break
                    file += df
                    rank += dr
            continue
        for df, dr in directions:
            file = frm_file + df
            rank = frm_rank + dr
            while 0 <= file < 8 and 0 <= rank < 8:
                to = make_square(file, rank)
                target = position.piece_at(to)
                if target == Piece.EMPTY:
                    _add_move(moves, position, frm, to, piece)
                else:
                    if _enemy(target, color) and target not in (Piece.WHITE_KING, Piece.BLACK_KING):
                        _add_move(moves, position, frm, to, piece)
                    break
                file += df
                rank += dr


def _generate_castling(position, moves, color):
    board = position.board
    enemy = color ^ 1
    if color == WHITE:
        king, rook = Piece.WHITE_KING, Piece.WHITE_ROOK
        if position.piece_at(E1) != king or is_square_attacked(position, E1, enemy):
            return
        if (
            position.castling_rights & WHITE_KINGSIDE
            and position.piece_at(H1) == rook
            and board.empty(F1) and board.empty(G1)
            and not is_square_attacked(position, F1, enemy)
            and not is_square_attacked(position, G1, enemy)
        ):
            moves.append(encode_move(E1, G1, king, flags=KING_CASTLE))
        if (
            position.castling_rights & WHITE_QUEENSIDE
            and position.piece_at(A1) == rook
            and board.empty(B1) and board.empty(C1) and board.empty(D1)
            and not is_square_attacked(position, D1, enemy)
            and not is_square_attacked(position, C1, enemy)
        ):
            moves.append(encode_move(E1, C1, king, flags=QUEEN_CASTLE))
    else:
        king, rook = Piece.BLACK_KING, Piece.BLACK_ROOK
        if position.piece_at(E8) != king or is_square_attacked(position, E8, enemy):
            return
        if (
            position.castling_rights & BLACK_KINGSIDE
            and position.piece_at(H8) == rook
            and board.empty(F8) and board.empty(G8)
            and not is_square_attacked(position, F8, enemy)
            and not is_square_attacked(position, G8, enemy)
        ):
            moves.append(encode_move(E8, G8, king, flags=KING_CASTLE))
        if (
            position.castling_rights & BLACK_QUEENSIDE
            and position.piece_at(A8) == rook
            and board.empty(B8) and board.empty(C8) and board.empty(D8)
            and not is_square_attacked(position, D8, enemy)
            and not is_square_attacked(position, C8, enemy)
        ):
            moves.append(encode_move(E8, C8, king, flags=QUEEN_CASTLE))


def generate_pseudo_legal_moves(position, tactical_only=False):
    """Generate moves obeying movement rules, but not all king-safety rules."""
    color = position.side_to_move
    moves = []
    _generate_pawns(position, moves, color, tactical_only)

    knight = Piece.WHITE_KNIGHT if color == WHITE else Piece.BLACK_KNIGHT
    bishop = Piece.WHITE_BISHOP if color == WHITE else Piece.BLACK_BISHOP
    rook = Piece.WHITE_ROOK if color == WHITE else Piece.BLACK_ROOK
    queen = Piece.WHITE_QUEEN if color == WHITE else Piece.BLACK_QUEEN
    king = Piece.WHITE_KING if color == WHITE else Piece.BLACK_KING

    _generate_leaper(position, moves, color, knight, KNIGHT_ATTACKS, tactical_only)
    _generate_slider(position, moves, color, (bishop, queen), DIAGONAL_DIRECTIONS, tactical_only)
    _generate_slider(position, moves, color, (rook, queen), ORTHOGONAL_DIRECTIONS, tactical_only)
    _generate_leaper(position, moves, color, king, KING_ATTACKS, tactical_only)
    if not tactical_only:
        _generate_castling(position, moves, color)
    return moves


def generate_legal_moves(position):
    """Generate legal moves using checker/pin masks for non-king moves."""
    color = position.side_to_move
    checkers, evasion_mask, pin_rays = _king_constraints(position, color)
    check_count = checkers.bit_count()
    legal = []
    for move in generate_pseudo_legal_moves(position):
        piece = moving_piece(move)
        frm = from_square(move)
        to = to_square(move)

        # King moves and en passant change attack occupancy in ways that are
        # deliberately validated through the trusted make/unmake path.
        if piece in (Piece.WHITE_KING, Piece.BLACK_KING) or is_en_passant(move):
            position.make_move(move)
            safe = not is_in_check(position, color)
            position.unmake_move()
            if safe:
                legal.append(move)
            continue

        if check_count >= 2:
            continue
        if check_count == 1 and not (evasion_mask & (1 << to)):
            continue
        pin_ray = pin_rays.get(frm)
        if pin_ray is not None and not (pin_ray & (1 << to)):
            continue
        legal.append(move)
    return legal


def _king_constraints(position, color):
    """Return checker bits, single-check evasion mask, and absolute pin rays."""
    board = position.board
    king = position.king_square(color)
    enemy = color ^ 1
    checkers = 0
    evasion_mask = 0
    pin_rays = {}

    enemy_knight = Piece.WHITE_KNIGHT if enemy == WHITE else Piece.BLACK_KNIGHT
    knight_checkers = KNIGHT_ATTACKS[king] & board.bitboard(enemy_knight)
    checkers |= knight_checkers
    evasion_mask |= knight_checkers

    enemy_king = Piece.WHITE_KING if enemy == WHITE else Piece.BLACK_KING
    king_checkers = KING_ATTACKS[king] & board.bitboard(enemy_king)
    checkers |= king_checkers
    evasion_mask |= king_checkers

    king_file = file_of(king)
    king_rank = rank_of(king)
    enemy_pawn = Piece.WHITE_PAWN if enemy == WHITE else Piece.BLACK_PAWN
    pawn_source_rank = king_rank - 1 if enemy == WHITE else king_rank + 1
    if 0 <= pawn_source_rank < 8:
        for pawn_file in (king_file - 1, king_file + 1):
            if 0 <= pawn_file < 8:
                square = make_square(pawn_file, pawn_source_rank)
                if board.piece_at(square) == enemy_pawn:
                    checkers |= 1 << square
                    evasion_mask |= 1 << square

    friendly_occ = board.white_occ if color == WHITE else board.black_occ
    enemy_bishop = Piece.WHITE_BISHOP if enemy == WHITE else Piece.BLACK_BISHOP
    enemy_rook = Piece.WHITE_ROOK if enemy == WHITE else Piece.BLACK_ROOK
    enemy_queen = Piece.WHITE_QUEEN if enemy == WHITE else Piece.BLACK_QUEEN

    for directions, sliders in (
        (DIAGONAL_DIRECTIONS, (enemy_bishop, enemy_queen)),
        (ORTHOGONAL_DIRECTIONS, (enemy_rook, enemy_queen)),
    ):
        for df, dr in directions:
            file = king_file + df
            rank = king_rank + dr
            ray = 0
            blocker = None
            while 0 <= file < 8 and 0 <= rank < 8:
                square = make_square(file, rank)
                ray |= 1 << square
                piece = board.piece_at(square)
                if piece != Piece.EMPTY:
                    if blocker is None and (friendly_occ & (1 << square)):
                        blocker = square
                    else:
                        if piece in sliders:
                            if blocker is None:
                                checkers |= 1 << square
                                evasion_mask |= ray
                            else:
                                pin_rays[blocker] = ray
                        break
                file += df
                rank += dr

    return checkers, evasion_mask, pin_rays


def _is_legal_by_make(position, move, color):
    position.make_move(move)
    try:
        return not is_in_check(position, color)
    finally:
        position.unmake_move()


def generate_legal_moves_reference(position):
    """Slow make/unmake legal generator retained as a correctness oracle."""
    color = position.side_to_move
    legal = []
    for move in generate_pseudo_legal_moves(position):
        if _is_legal_by_make(position, move, color):
            legal.append(move)
    return legal


def generate_legal_tactical_moves(position):
    """Generate legal captures and promotions for quiescence search."""
    color = position.side_to_move
    checkers, evasion_mask, pin_rays = _king_constraints(position, color)
    check_count = checkers.bit_count()
    legal = []
    for move in generate_pseudo_legal_moves(position, tactical_only=True):
        piece = moving_piece(move)
        frm = from_square(move)
        to = to_square(move)
        if piece in (Piece.WHITE_KING, Piece.BLACK_KING) or is_en_passant(move):
            if _is_legal_by_make(position, move, color):
                legal.append(move)
            continue
        if check_count >= 2:
            continue
        if check_count == 1 and not (evasion_mask & (1 << to)):
            continue
        pin_ray = pin_rays.get(frm)
        if pin_ray is not None and not (pin_ray & (1 << to)):
            continue
        legal.append(move)
    return legal


def has_legal_move(position):
    """Return after finding the first legal move."""
    color = position.side_to_move
    for move in generate_pseudo_legal_moves(position):
        position.make_move(move)
        legal = not is_in_check(position, color)
        position.unmake_move()
        if legal:
            return True
    return False
