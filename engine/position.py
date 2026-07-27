"""Complete chess position state and reversible move application."""

from .board import Board
from .castling import CASTLING_MASK
from .constants import BLACK, NO_EN_PASSANT, WHITE
from .history import History
from .move import (
    captured_piece,
    from_square,
    is_double_push,
    is_en_passant,
    is_kingside_castle,
    is_promotion,
    is_queenside_castle,
    moving_piece,
    promotion_piece,
    to_square,
)
from .pieces import Piece, is_pawn
from .squares import A1, A8, D1, D8, F1, F8, H1, H8
from .undo import UndoState
from .zobrist import (
    castling_hash,
    compute_hash,
    en_passant_hash,
    piece_hash,
    side_hash,
)


class Position:
    """Owns piece placement, rule state, hash, and move history."""

    def __init__(self):
        self.board = Board()
        self.side_to_move = WHITE
        self.castling_rights = 0
        self.en_passant = NO_EN_PASSANT
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.white_king_square = -1
        self.black_king_square = -1
        self.hash_key = 0
        self.history = History()

    def clear(self):
        self.board.clear()
        self.side_to_move = WHITE
        self.castling_rights = 0
        self.en_passant = NO_EN_PASSANT
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.white_king_square = -1
        self.black_king_square = -1
        self.hash_key = 0
        self.history.clear()

    def piece_at(self, square):
        return self.board.piece_at(square)

    def occupied(self, square):
        return self.board.occupied(square)

    def king_square(self, color):
        return self.white_king_square if color == WHITE else self.black_king_square

    def set_king_square(self, color, square):
        if color == WHITE:
            self.white_king_square = square
        else:
            self.black_king_square = square

    def add_piece(self, square, piece):
        self.board.add_piece(square, piece)
        self.hash_key ^= piece_hash(piece, square)
        if piece == Piece.WHITE_KING:
            self.white_king_square = square
        elif piece == Piece.BLACK_KING:
            self.black_king_square = square

    def remove_piece(self, square):
        piece = self.board.piece_at(square)
        if piece == Piece.EMPTY:
            return Piece.EMPTY
        self.hash_key ^= piece_hash(piece, square)
        self.board.remove_piece(square)
        if piece == Piece.WHITE_KING:
            self.white_king_square = -1
        elif piece == Piece.BLACK_KING:
            self.black_king_square = -1
        return piece

    def move_piece(self, frm, to):
        piece = self.piece_at(frm)
        if piece == Piece.EMPTY:
            raise ValueError(f"No piece on square {frm}")
        if self.piece_at(to) != Piece.EMPTY:
            raise ValueError(f"Destination square {to} is occupied")
        self.hash_key ^= piece_hash(piece, frm)
        self.board.move_piece(frm, to)
        self.hash_key ^= piece_hash(piece, to)
        if piece == Piece.WHITE_KING:
            self.white_king_square = to
        elif piece == Piece.BLACK_KING:
            self.black_king_square = to

    def make_move(self, move):
        """Apply an encoded pseudo-legal move and save one undo record."""
        frm = from_square(move)
        to = to_square(move)
        piece = moving_piece(move)

        if self.piece_at(frm) != piece:
            raise ValueError("Moving piece does not match the board")

        undo = UndoState(
            move=move,
            castling_rights=self.castling_rights,
            en_passant=self.en_passant,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            hash_key=self.hash_key,
        )

        expected_capture = captured_piece(move)
        if is_en_passant(move):
            capture_square = to - 8 if self.side_to_move == WHITE else to + 8
        else:
            capture_square = to

        actual_capture = self.piece_at(capture_square)
        if expected_capture != actual_capture:
            raise ValueError("Captured piece does not match the board")
        if actual_capture != Piece.EMPTY:
            undo.captured_piece = actual_capture
            undo.captured_square = capture_square
            self.remove_piece(capture_square)

        self.move_piece(frm, to)

        if is_promotion(move):
            promoted = promotion_piece(move)
            if promoted == Piece.EMPTY:
                raise ValueError("Promotion move has no promotion piece")
            self.remove_piece(to)
            self.add_piece(to, promoted)
        elif is_kingside_castle(move):
            rook_from, rook_to = (H1, F1) if self.side_to_move == WHITE else (H8, F8)
            self.move_piece(rook_from, rook_to)
        elif is_queenside_castle(move):
            rook_from, rook_to = (A1, D1) if self.side_to_move == WHITE else (A8, D8)
            self.move_piece(rook_from, rook_to)

        self.hash_key ^= castling_hash(self.castling_rights)
        self.castling_rights &= CASTLING_MASK[frm]
        self.castling_rights &= CASTLING_MASK[to]
        self.hash_key ^= castling_hash(self.castling_rights)

        if self.en_passant != NO_EN_PASSANT:
            self.hash_key ^= en_passant_hash(self.en_passant)
        self.en_passant = NO_EN_PASSANT
        if is_double_push(move):
            self.en_passant = frm + 8 if self.side_to_move == WHITE else frm - 8
            self.hash_key ^= en_passant_hash(self.en_passant)

        self.halfmove_clock = (
            0 if is_pawn(piece) or actual_capture != Piece.EMPTY
            else self.halfmove_clock + 1
        )
        if self.side_to_move == BLACK:
            self.fullmove_number += 1

        self.side_to_move ^= 1
        self.hash_key ^= side_hash()
        self.history.push(undo)

        if self.hash_key != compute_hash(self):
            raise AssertionError("Incremental hash mismatch after make_move")

    def unmake_move(self):
        """Restore the exact state before the most recent move."""
        if self.history.empty():
            raise ValueError("Cannot unmake move: history is empty")

        undo = self.history.pop()
        move = undo.move
        frm = from_square(move)
        to = to_square(move)

        self.side_to_move ^= 1

        if is_kingside_castle(move):
            rook_from, rook_to = (F1, H1) if self.side_to_move == WHITE else (F8, H8)
            self.move_piece(rook_from, rook_to)
        elif is_queenside_castle(move):
            rook_from, rook_to = (D1, A1) if self.side_to_move == WHITE else (D8, A8)
            self.move_piece(rook_from, rook_to)

        if is_promotion(move):
            self.remove_piece(to)
            self.add_piece(to, moving_piece(move))

        self.move_piece(to, frm)
        if undo.captured_piece != Piece.EMPTY:
            self.add_piece(undo.captured_square, undo.captured_piece)

        undo.restore_position(self)

        if self.hash_key != compute_hash(self):
            raise AssertionError("Hash mismatch after unmake_move")

    def print(self):
        self.board.print_board()

    def __eq__(self, other):
        return (
            isinstance(other, Position)
            and self.board == other.board
            and self.side_to_move == other.side_to_move
            and self.castling_rights == other.castling_rights
            and self.en_passant == other.en_passant
            and self.halfmove_clock == other.halfmove_clock
            and self.fullmove_number == other.fullmove_number
            and self.white_king_square == other.white_king_square
            and self.black_king_square == other.black_king_square
            and self.hash_key == other.hash_key
        )
