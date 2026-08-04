"""
undo.py

Stores the irreversible information required to restore
a previous chess position.

UndoState records are pooled by History and reused at each search ply.

It contains only the information that cannot always be
reconstructed from the board after a move.

The search stores these objects inside History.
"""

from dataclasses import dataclass

from .pieces import Piece
from .constants import NO_EN_PASSANT
@dataclass(slots=True)
class UndoState:
    """
    Represents one entry in the history stack.

    This stores the previous irreversible state of the
    position before a move was made.
    """

    # -----------------------------
    # Move Information
    # -----------------------------

    move: int = 0

    captured_piece: Piece = Piece.EMPTY
    captured_square: int = -1

    # -----------------------------
    # Rule State
    # -----------------------------

    castling_rights: int = 0

    en_passant: int = NO_EN_PASSANT

    halfmove_clock: int = 0

    fullmove_number: int = 1

    # -----------------------------
    # Hash
    # -----------------------------

    hash_key: int = 0
    def save_position(self, position):
        """
        Saves the irreversible state
        from a Position.
        """

        self.castling_rights = position.castling_rights

        self.en_passant = position.en_passant

        self.halfmove_clock = position.halfmove_clock

        self.fullmove_number = position.fullmove_number

        self.hash_key = position.hash_key
    def restore_position(self, position):
        """
        Restores the irreversible state
        back into Position.
        """

        position.castling_rights = self.castling_rights

        position.en_passant = self.en_passant

        position.halfmove_clock = self.halfmove_clock

        position.fullmove_number = self.fullmove_number

        position.hash_key = self.hash_key
    def clear(self):
        """
        Resets the undo state.
        """

        self.move = 0

        self.captured_piece = Piece.EMPTY

        self.castling_rights = 0

        self.en_passant = NO_EN_PASSANT

        self.halfmove_clock = 0

        self.fullmove_number = 1

        self.hash_key = 0
    def __str__(self):

        return (
            "UndoState("
            f"captured={self.captured_piece}, "
            f"castle={self.castling_rights}, "
            f"ep={self.en_passant}, "
            f"half={self.halfmove_clock}, "
            f"full={self.fullmove_number}"
            ")"
        )
