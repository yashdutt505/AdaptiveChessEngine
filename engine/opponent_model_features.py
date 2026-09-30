"""Versioned features for predicting a side-to-move player's large error."""

from __future__ import annotations

from .attacks import is_in_check, is_square_attacked
from .bitboard import bits
from .constants import BLACK, WHITE
from .evaluation import FILE_MASKS, PIECE_VALUES, _king_safety, _mobility, _pawn_scores
from .fen import load_fen
from .move import is_capture
from .movegen import generate_legal_moves
from .pieces import Piece
from .position import Position


MODEL_FEATURE_SET_ID = "ace.opponent-error-position.v1"
MODEL_FEATURE_NAMES = (
    "in_check",
    "legal_move_count",
    "legal_capture_count",
    "material_balance_cp",
    "material_imbalance_cp",
    "remaining_non_pawn_material_cp",
    "remaining_pawn_count",
    "open_file_count",
    "mobility_balance",
    "king_safety_balance",
    "pawn_structure_balance",
    "center_control_balance",
    "pawn_tension_count",
    "fullmove_number",
    "side_to_move_is_black",
    "player_rating",
    "rating_difference",
)


def _material(position: Position, color: int, include_pawns: bool = True) -> int:
    first = Piece.WHITE_PAWN if color == WHITE else Piece.BLACK_PAWN
    last = Piece.WHITE_QUEEN if color == WHITE else Piece.BLACK_QUEEN
    total = 0
    for piece in range(first, last + 1):
        if not include_pawns and piece in (Piece.WHITE_PAWN, Piece.BLACK_PAWN):
            continue
        total += PIECE_VALUES[piece] * position.board.bitboard(piece).bit_count()
    return total


def _center_control(position: Position, color: int) -> int:
    return sum(is_square_attacked(position, square, color) for square in (27, 28, 35, 36))


def _pawn_tensions(position: Position) -> int:
    white_pawns = position.board.bitboard(Piece.WHITE_PAWN)
    black_pawns = position.board.bitboard(Piece.BLACK_PAWN)
    total = 0
    for square in bits(white_pawns):
        rank, file = divmod(square, 8)
        if rank == 7:
            continue
        for target_file in (file - 1, file + 1):
            if 0 <= target_file < 8 and black_pawns & (1 << ((rank + 1) * 8 + target_file)):
                total += 1
    return total


def extract_position_features(
    fen: str, player_rating: int | None, opponent_rating: int | None,
) -> dict[str, int]:
    """Measure the position from the vulnerable side-to-move perspective."""
    position = Position()
    load_fen(position, fen)
    player = position.side_to_move
    opponent = player ^ 1
    legal = generate_legal_moves(position)
    player_material = _material(position, player)
    opponent_material = _material(position, opponent)
    balance = player_material - opponent_material
    white_pawns = position.board.bitboard(Piece.WHITE_PAWN)
    black_pawns = position.board.bitboard(Piece.BLACK_PAWN)
    pawn_scores = _pawn_scores(white_pawns, black_pawns)
    rating = player_rating if player_rating is not None else 0
    rating_difference = (
        player_rating - opponent_rating
        if player_rating is not None and opponent_rating is not None else 0
    )
    values = {
        "in_check": int(is_in_check(position, player)),
        "legal_move_count": len(legal),
        "legal_capture_count": sum(is_capture(move) for move in legal),
        "material_balance_cp": balance,
        "material_imbalance_cp": abs(balance),
        "remaining_non_pawn_material_cp": _material(position, WHITE, False) + _material(position, BLACK, False),
        "remaining_pawn_count": (white_pawns | black_pawns).bit_count(),
        "open_file_count": sum(not ((white_pawns | black_pawns) & mask) for mask in FILE_MASKS),
        "mobility_balance": _mobility(position, player) - _mobility(position, opponent),
        "king_safety_balance": _king_safety(position, player) - _king_safety(position, opponent),
        "pawn_structure_balance": pawn_scores[player] - pawn_scores[opponent],
        "center_control_balance": _center_control(position, player) - _center_control(position, opponent),
        "pawn_tension_count": _pawn_tensions(position),
        "fullmove_number": position.fullmove_number,
        "side_to_move_is_black": int(player == BLACK),
        "player_rating": rating,
        "rating_difference": rating_difference,
    }
    assert tuple(values) == MODEL_FEATURE_NAMES
    return values


def model_row(analyzed: dict) -> dict:
    if not analyzed.get("label_eligible"):
        raise ValueError("cannot build a model row from an ineligible label")
    return {
        "feature_set": MODEL_FEATURE_SET_ID,
        "game_id": analyzed["game_id"],
        "ply": analyzed["ply"],
        "split": analyzed["split"],
        "features": extract_position_features(
            analyzed["fen_before"], analyzed.get("player_rating"), analyzed.get("opponent_rating"),
        ),
        "large_error": bool(analyzed["large_error"]),
        "centipawn_loss": analyzed["centipawn_loss"],
    }
