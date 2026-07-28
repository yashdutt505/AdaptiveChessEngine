"""Pseudo-legal and fully legal chess move generation."""

from .attacks import (
    DIAGONAL_DIRECTIONS,
    KING_DELTAS,
    KNIGHT_DELTAS,
    ORTHOGONAL_DIRECTIONS,
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
from .move import (
    CAPTURE,
    DOUBLE_PAWN_PUSH,
    EN_PASSANT,
    KING_CASTLE,
    PROMOTION,
    QUEEN_CASTLE,
    encode_move,
    is_capture,
    is_promotion,
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


def _generate_pawns(position, moves, color):
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

    for frm in range(64):
        if board.piece_at(frm) != pawn:
            continue
        file = file_of(frm)
        rank = rank_of(frm)
        next_rank = rank + direction

        if 0 <= next_rank < 8:
            to = make_square(file, next_rank)
            if board.empty(to):
                if next_rank == promotion_rank:
                    for promoted in promotions:
                        moves.append(encode_move(frm, to, pawn, promotion_piece=promoted, flags=PROMOTION))
                else:
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


def _generate_leaper(position, moves, color, piece, deltas):
    for frm in range(64):
        if position.piece_at(frm) != piece:
            continue
        frm_file = file_of(frm)
        frm_rank = rank_of(frm)
        for df, dr in deltas:
            file = frm_file + df
            rank = frm_rank + dr
            if not (0 <= file < 8 and 0 <= rank < 8):
                continue
            to = make_square(file, rank)
            target = position.piece_at(to)
            if not _friendly(target, color) and target not in (Piece.WHITE_KING, Piece.BLACK_KING):
                _add_move(moves, position, frm, to, piece)


def _generate_slider(position, moves, color, pieces, directions):
    for frm in range(64):
        piece = position.piece_at(frm)
        if piece not in pieces:
            continue
        frm_file = file_of(frm)
        frm_rank = rank_of(frm)
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


def generate_pseudo_legal_moves(position):
    """Generate moves obeying movement rules, but not all king-safety rules."""
    color = position.side_to_move
    moves = []
    _generate_pawns(position, moves, color)

    knight = Piece.WHITE_KNIGHT if color == WHITE else Piece.BLACK_KNIGHT
    bishop = Piece.WHITE_BISHOP if color == WHITE else Piece.BLACK_BISHOP
    rook = Piece.WHITE_ROOK if color == WHITE else Piece.BLACK_ROOK
    queen = Piece.WHITE_QUEEN if color == WHITE else Piece.BLACK_QUEEN
    king = Piece.WHITE_KING if color == WHITE else Piece.BLACK_KING

    _generate_leaper(position, moves, color, knight, KNIGHT_DELTAS)
    _generate_slider(position, moves, color, (bishop, queen), DIAGONAL_DIRECTIONS)
    _generate_slider(position, moves, color, (rook, queen), ORTHOGONAL_DIRECTIONS)
    _generate_leaper(position, moves, color, king, KING_DELTAS)
    _generate_castling(position, moves, color)
    return moves


def generate_legal_moves(position):
    """Generate only moves that leave the moving side's king safe."""
    color = position.side_to_move
    legal = []
    for move in generate_pseudo_legal_moves(position):
        position.make_move(move)
        if not is_in_check(position, color):
            legal.append(move)
        position.unmake_move()
    return legal


def generate_legal_tactical_moves(position):
    """Generate legal captures and promotions for quiescence search."""
    color = position.side_to_move
    legal = []
    for move in generate_pseudo_legal_moves(position):
        if not (is_capture(move) or is_promotion(move)):
            continue
        position.make_move(move)
        if not is_in_check(position, color):
            legal.append(move)
        position.unmake_move()
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
