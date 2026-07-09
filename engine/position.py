"""
position.py

Stores the complete game state.

This class owns:

- Board
- Side to move
- Castling rights
- En passant square
- Halfmove clock
- Fullmove number
- King locations
- Hash key
- History
"""

from .board import Board
from .history import History
from .pieces import *
from .constants import *
from .move import *
from .undo import UndoState
from .zobrist import piece_hash
from .zobrist import side_hash
from .zobrist import castling_hash
from .zobrist import en_passant_hash
from .hash_debug import verify_incremental_hash
from .castling import *
from .zobrist import compute_hash
from engine import undo
class Position:

    def __init__(self):

        self.board = Board()

        # -------------------------------------------------
        # Game State
        # -------------------------------------------------

        self.side_to_move = WHITE

        self.castling_rights = 0

        self.en_passant = NO_EN_PASSANT

        self.halfmove_clock = 0

        self.fullmove_number = 1

        # -------------------------------------------------
        # King Squares
        # -------------------------------------------------

        self.white_king_square = -1
        self.black_king_square = -1

        # -------------------------------------------------
        # Hash
        # -------------------------------------------------

        self.hash_key = 0

        # -------------------------------------------------
        # Move History
        # -------------------------------------------------

        self.history = History()

    # =====================================================
    # Reset Position
    # =====================================================

    def clear(self):

        self.board.clear()

        self.side_to_move = WHITE

        self.castling_rights = 0

        self.en_passant = -1

        self.halfmove_clock = 0

        self.fullmove_number = 1

        self.white_king_square = -1

        self.black_king_square = -1

        self.hash_key = 0

        self.history = History()

    # =====================================================
    # Helpers
    # =====================================================

    def piece_at(self, square):

        return self.board.piece_at(square)

    def occupied(self, square):

        return self.board.occupied(square)

    def king_square(self, color):

        if color == WHITE:
            return self.white_king_square

        return self.black_king_square

    def set_king_square(self, color, square):

        if color == WHITE:
            self.white_king_square = square
        else:
            self.black_king_square = square

    # =====================================================
    # Piece Management
    # =====================================================

    def add_piece(self, square, piece):

        self.board.add_piece(square, piece)

        # ----------------------------
        # Incremental Hash
        # ----------------------------

        self.hash_key ^= piece_hash(
            piece,
            square
        )

        if piece == Piece.WHITE_KING:
            self.white_king_square = square

        elif piece == Piece.BLACK_KING:
            self.black_king_square = square

    def remove_piece(self, square):

        piece = self.board.piece_at(square)

        if piece == Piece.EMPTY:
            return Piece.EMPTY

        # -----------------------------------------
        # Incremental Hash
        # -----------------------------------------

        self.hash_key ^= piece_hash(
            piece,
            square
        )

        self.board.remove_piece(square)

        if piece == Piece.WHITE_KING:
            self.white_king_square = -1

        elif piece == Piece.BLACK_KING:
            self.black_king_square = -1

        return piece

    def move_piece(self, frm, to):
        """
        Moves a piece from one square to another.

        Captures are handled here instead of inside Board
        so Position remains responsible for all state changes.
        """

        piece = self.board.piece_at(frm)

        if piece == Piece.EMPTY:
            raise ValueError(f"No piece on square {frm}")

        captured = Piece.EMPTY

        # -----------------------------------------
        # Handle capture
        # -----------------------------------------

        if not self.board.empty(to):

            captured = self.remove_piece(to)

        # -----------------------------------------
        # Remove moving piece hash
        # -----------------------------------------

        self.hash_key ^= piece_hash(piece, frm)

        # -----------------------------------------
        # Move piece on board
        # -----------------------------------------

        self.board.move_piece(frm, to)

        # -----------------------------------------
        # Add moving piece hash
        # -----------------------------------------

        self.hash_key ^= piece_hash(piece, to)

        # -----------------------------------------
        # Update king squares
        # -----------------------------------------

        if piece == Piece.WHITE_KING:
            self.white_king_square = to

        elif piece == Piece.BLACK_KING:
            self.black_king_square = to

        return captured
    # =====================================================
    # History Helpers
    # =====================================================

    def _push_undo(self, undo: UndoState):

        self.history.push(undo)


    def _pop_undo(self) -> UndoState:

        return self.history.pop()
    # =====================================================
    # Save Undo
    # =====================================================

    def _save_undo(self, move: int) -> UndoState:
        """
        Saves everything needed to restore
        the current position later.
        """

        undo = UndoState()

        undo.move = move

        undo.save_position(self)

        undo.captured_piece = captured_piece(move)

        self._push_undo(undo)

        return undo
    # =====================================================
    # Make Move
    # =====================================================

    def _create_undo_state(self, move):
        """
        Creates an UndoState describing the
        current position before a move is made.
        """

        undo = UndoState()

        undo.move = move

        undo.castling_rights = self.castling_rights

        undo.en_passant = self.en_passant

        undo.halfmove_clock = self.halfmove_clock

        undo.fullmove_number = self.fullmove_number

        undo.hash_key = self.hash_key

        return undo
    def make_move(self, move: int):
        """
        Applies a move to the position.

        The implementation is intentionally
        broken into small helper methods.
        """

        self._save_undo(move)

        self._move_piece(move)
        print(f"Stored : {self.hash_key:016X}")
        print(f"Actual : {compute_hash(self):016X}")    

        self._handle_special_moves(move)

        self._update_castling_rights(move)

        self._update_en_passant(move)

        self._update_move_counters(move)

       
        self._toggle_side_to_move()

        verify_incremental_hash(self)

    def unmake_move(self):
        """
        Restores the previous position.

        The last UndoState is popped from the
        history stack and used to restore the
        game state.
        """

        if self.history.empty():
            raise ValueError(
                "Cannot unmake move. History is empty."
            )

        undo = self.history.pop()

        self._restore_side()

        self._restore_move(undo)

        self._restore_special_move(undo)

        self._restore_irreversible_state(undo)

        verify_incremental_hash(self)
    def _restore_side(self):
        """
        Restores the side to move.

        This is exactly the reverse of the final
        step performed by make_move().
        """

        self._toggle_side_to_move()


    def _restore_move(self, undo):
        """
        Restores the moved piece and any captured piece.

        Handles:
            - normal moves
            - captures

        Does NOT handle:
            - castling
            - en passant
            - promotion
        """

        move = undo.move

        frm = from_square(move)
        to = to_square(move)

        piece = moving_piece(move)

        # -----------------------------------------
        # Move piece back
        # -----------------------------------------

        self.move_piece(to, frm)

        # -----------------------------------------
        # Restore captured piece
        # -----------------------------------------

        if (
            undo.captured_piece != Piece.EMPTY
            and
            not is_en_passant(move)
        ):

            self.add_piece(
                undo.captured_square,
                undo.captured_piece
            )                               


    def _restore_special_move(self, undo):
        """
        Restores special moves.

        Handles:
            - promotion
            - castling
            - en passant
        """

        move = undo.move

        # -----------------------------------------
        # Promotion
        # -----------------------------------------

        if is_promotion(move):

            self.remove_piece(from_square(move))

            self.add_piece(
                from_square(move),
                moving_piece(move)
            )

            return

        # -----------------------------------------
        # Kingside Castling
        # -----------------------------------------

        if is_kingside_castle(move):

            # White
            if self.side_to_move == WHITE:

                self.move_piece(
                    square_from_string("f1"),
                    square_from_string("h1")
                )

            # Black
            else:

                self.move_piece(
                    square_from_string("f8"),
                    square_from_string("h8")
                )

            return

        # -----------------------------------------
        # Queenside Castling
        # -----------------------------------------

        if is_queenside_castle(move):

            if self.side_to_move == WHITE:

                self.move_piece(
                    square_from_string("d1"),
                    square_from_string("a1")
                )

            else:

                self.move_piece(
                    square_from_string("d8"),
                    square_from_string("a8")
                )

            return

        # -----------------------------------------
        # En Passant
        # -----------------------------------------

        if is_en_passant(move):

            self.add_piece(
                undo.captured_square,
                undo.captured_piece
            )

    def _restore_irreversible_state(self, undo):
        """
        Restores irreversible information
        from the UndoState.
        """

        undo.restore_position(self)
    # =====================================================
    # Internal Move Helpers
    # =====================================================

    def _move_piece(self, move):
        """
        Performs the basic piece movement.

        Handles:
            - normal moves
            - captures

        Does NOT handle:
            - castling
            - en passant
            - promotion

        Also creates and stores the UndoState
        before modifying the position.
        """

        frm = from_square(move)
        to = to_square(move)

        piece = moving_piece(move)
        expected_capture = captured_piece(move)

        # -----------------------------------------
        # Safety Checks
        # -----------------------------------------

        board_piece = self.piece_at(frm)

        if board_piece != piece:
            raise ValueError(
                f"Move mismatch.\n"
                f"Expected piece {piece} on {frm}\n"
                f"Found {board_piece}"
            )

        # -----------------------------------------
        # Create Undo State
        # -----------------------------------------

        undo = self._create_undo_state(move)

        # -----------------------------------------
        # Capture
        # -----------------------------------------

        if expected_capture != Piece.EMPTY and not is_en_passant(move):

            actual_piece = self.piece_at(to)

            if actual_piece != expected_capture:
                raise ValueError(
                    "Captured piece mismatch."
                )

            undo.captured_piece = actual_piece
            undo.captured_square = to

            self.remove_piece(to)

        # -----------------------------------------
        # Save Undo State
        # -----------------------------------------

        self.history.push(undo)

        # -----------------------------------------
        # Move Piece
        # -----------------------------------------

        self.move_piece(frm, to)


    def _handle_special_moves(self, move):
        """
        Handles all special chess moves.

        At this stage this function only
        dispatches to helper functions.
        """

        if is_en_passant(move):
            self._handle_en_passant(move)

        elif is_kingside_castle(move):
            self._handle_kingside_castle()

        elif is_queenside_castle(move):
            self._handle_queenside_castle()

        elif is_promotion(move):
            self._handle_promotion(move)

        
    def _handle_en_passant(self, move):
        """
        Handles an en passant capture.

        The moving pawn has already been moved
        by _move_piece().

        Only the captured pawn remains to
        be removed.
        """

        to = to_square(move)

        if self.side_to_move == WHITE:
            captured_square = to - 8
        else:
            captured_square = to + 8

        # ----------------------------
        # Save captured pawn in undo
        # ----------------------------
        captured_piece = self.piece_at(captured_square)

        if captured_piece == Piece.EMPTY:
            raise ValueError(
                "No pawn found for en passant capture."
            )   
        undo = self.history.peek()

        captured_piece = self.piece_at(captured_square)

        undo.captured_piece = captured_piece
        undo.captured_square = captured_square

        # ----------------------------
        # Remove captured pawn
        # ----------------------------

        self.remove_piece(captured_square)


    def _handle_kingside_castle(self):
        """
        Moves the rook during a kingside castle.

        The king has already been moved by
        _move_piece().
        """

        if self.side_to_move == WHITE:

            # h1 -> f1
            self.move_piece(7, 5)

        else:

            # h8 -> f8
            self.move_piece(63, 61)


    def _handle_queenside_castle(self):
        """
        Moves the rook during a queenside castle.

        The king has already been moved by
        _move_piece().
        """

        if self.side_to_move == WHITE:

            # a1 -> d1
            self.move_piece(0, 3)

        else:

            # a8 -> d8
            self.move_piece(56, 59)

    def _handle_promotion(self, move):
        """
        Replaces a pawn with its promoted piece.

        At this point the pawn has already been moved
        to the promotion square by _move_piece().
        """

        to = to_square(move)

        promoted = promotion_piece(move)

        # -----------------------------------------
        # Safety Check
        # -----------------------------------------

        if promoted == Piece.EMPTY:
            raise ValueError(
                "Promotion move has no promoted piece."
            )

        # -----------------------------------------
        # Replace Pawn
        # -----------------------------------------

        self.remove_piece(to)

        self.add_piece(to, promoted)


    def _update_castling_rights(self, move):
        """
        Updates castling rights and their
        Zobrist hash.
        """

        frm = from_square(move)
        to = to_square(move)

        # Remove old rights from hash
        self.hash_key ^= castling_hash(
            self.castling_rights
        )

        # Update rights
        self.castling_rights &= CASTLING_MASK[frm]
        self.castling_rights &= CASTLING_MASK[to]

        # Add new rights
        self.hash_key ^= castling_hash(
            self.castling_rights
        )


    def _update_en_passant(self, move):
        """
        Updates the en passant square and
        its Zobrist hash.
        """

        # ---------------------------------
        # Remove old EP hash
        # ---------------------------------

        if self.en_passant != NO_EN_PASSANT:
            self.hash_key ^= en_passant_hash(
                self.en_passant
            )

        # ---------------------------------
        # Clear EP
        # ---------------------------------

        self.en_passant = NO_EN_PASSANT

        # ---------------------------------
        # Double pawn push creates one
        # ---------------------------------

        if is_double_push(move):

            frm = from_square(move)

            if self.side_to_move == WHITE:
                self.en_passant = frm + 8
            else:
                self.en_passant = frm - 8

        # ---------------------------------
        # Add new EP hash
        # ---------------------------------

        if self.en_passant != NO_EN_PASSANT:
            self.hash_key ^= en_passant_hash(
                self.en_passant
            )

    def _update_move_counters(self, move):
        """
        Updates the halfmove clock and
        fullmove number.
        """

        piece = moving_piece(move)

        # -----------------------------------------
        # Halfmove clock
        # -----------------------------------------

        if (
            is_pawn(piece)
            or
            is_capture(move)
            or
            is_en_passant(move)
        ):

            self.halfmove_clock = 0

        else:

            self.halfmove_clock += 1

        # -----------------------------------------
        # Fullmove number
        # -----------------------------------------

        if self.side_to_move == BLACK:
            self.fullmove_number += 1




    def _toggle_side_to_move(self):
        """
        Switches the side to move and updates
        the Zobrist hash.
        """

        # Remove/Add side key
        self.hash_key ^= side_hash()

        if self.side_to_move == WHITE:
            self.side_to_move = BLACK
        else:
            self.side_to_move = WHITE
    # =====================================================
    # Debug
    # =====================================================

    def print(self):

        self.board.print_board()

        print()

        print("Side to move :", "White" if self.side_to_move == WHITE else "Black")
        print("Castling     :", self.castling_rights)
        print("En Passant   :", self.en_passant)
        print("Halfmove     :", self.halfmove_clock)
        print("Fullmove     :", self.fullmove_number)
        print("White King   :", self.white_king_square)
        print("Black King   :", self.black_king_square)
    def __eq__(self, other):
        """
        Compares two positions for equality.
        """

        if not isinstance(other, Position):
            return False

        return (
            self.board == other.board
            and self.side_to_move == other.side_to_move
            and self.castling_rights == other.castling_rights
            and self.en_passant == other.en_passant
            and self.halfmove_clock == other.halfmove_clock
            and self.fullmove_number == other.fullmove_number
            and self.white_king_square == other.white_king_square
            and self.black_king_square == other.black_king_square
            and self.hash_key == other.hash_key
        )