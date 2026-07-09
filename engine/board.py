"""
board.py

Core board representation used by the engine.

The Board class stores ONLY information about piece placement.

Game state such as:

- side to move
- castling rights
- en passant
- move counters
- hash key

belongs inside Position.

Representations maintained simultaneously:

1. Mailbox (64-square array)
2. 12 piece bitboards
3. White occupancy
4. Black occupancy
5. All occupancy

All representations are always kept synchronized.
"""

from .pieces import *
from .bitboard import *


class Board:
    """
    Low-level board representation.

    This class does not know anything about legal chess moves.

    It only knows where pieces are.
    """

    def __init__(self):

        self.clear()

    # =====================================================
    # Reset Board
    # =====================================================

    def clear(self):

        # -----------------------------------------
        # Mailbox
        # -----------------------------------------

        self.squares = [Piece.EMPTY] * 64

        # -----------------------------------------
        # Piece Bitboards
        #
        # Index:
        #
        # 1 White Pawn
        # ...
        # 12 Black King
        # -----------------------------------------

        self.bitboards = [0] * 13

        # -----------------------------------------
        # Occupancies
        # -----------------------------------------

        self.white_occ = 0

        self.black_occ = 0

        self.all_occ = 0

    # =====================================================
    # Basic Queries
    # =====================================================

    def piece_at(self, square: int) -> Piece:

        return self.squares[square]

    def occupied(self, square: int) -> bool:

        return get_bit(self.all_occ, square)

    def empty(self, square: int) -> bool:

        return self.squares[square] == Piece.EMPTY

    # =====================================================
    # Piece Bitboards
    # =====================================================

    def piece_bb(self, piece: Piece):

        return self.bitboards[piece]

    def white_pawns(self):
        return self.bitboards[Piece.WHITE_PAWN]

    def white_knights(self):
        return self.bitboards[Piece.WHITE_KNIGHT]

    def white_bishops(self):
        return self.bitboards[Piece.WHITE_BISHOP]

    def white_rooks(self):
        return self.bitboards[Piece.WHITE_ROOK]

    def white_queens(self):
        return self.bitboards[Piece.WHITE_QUEEN]

    def white_king(self):
        return self.bitboards[Piece.WHITE_KING]

    def black_pawns(self):
        return self.bitboards[Piece.BLACK_PAWN]

    def black_knights(self):
        return self.bitboards[Piece.BLACK_KNIGHT]

    def black_bishops(self):
        return self.bitboards[Piece.BLACK_BISHOP]

    def black_rooks(self):
        return self.bitboards[Piece.BLACK_ROOK]

    def black_queens(self):
        return self.bitboards[Piece.BLACK_QUEEN]

    def black_king(self):
        return self.bitboards[Piece.BLACK_KING]
    # =====================================================
    # Internal Helpers
    # =====================================================

    def _set_piece_bit(self, piece: Piece, square: int):
        """
        Sets a bit for a specific piece bitboard.
        """
        self.bitboards[piece] = set_bit(
            self.bitboards[piece],
            square
        )

    def _clear_piece_bit(self, piece: Piece, square: int):
        """
        Clears a bit for a specific piece bitboard.
        """
        self.bitboards[piece] = clear_bit(
            self.bitboards[piece],
            square
        )

    def _set_occupancy(self, piece: Piece, square: int):
        """
        Adds square to occupancy bitboards.
        """

        if is_white(piece):
            self.white_occ = set_bit(
                self.white_occ,
                square
            )

        elif is_black(piece):
            self.black_occ = set_bit(
                self.black_occ,
                square
            )

        self.all_occ = set_bit(
            self.all_occ,
            square
        )

    def _clear_occupancy(self, piece: Piece, square: int):
        """
        Removes square from occupancy bitboards.
        """

        if is_white(piece):
            self.white_occ = clear_bit(
                self.white_occ,
                square
            )

        elif is_black(piece):
            self.black_occ = clear_bit(
                self.black_occ,
                square
            )

        self.all_occ = clear_bit(
            self.all_occ,
            square)

    # =====================================================
    # Piece Manipulation
    # =====================================================

    def add_piece(self, square: int, piece: Piece):
        """
        Adds a piece onto an empty square.
        """

        if piece == Piece.EMPTY:
            raise ValueError("Cannot add EMPTY piece.")

        if not self.empty(square):
            raise ValueError(
                f"Square {square} already occupied."
            )

        self.squares[square] = piece

        self._set_piece_bit(piece, square)

        self._set_occupancy(piece, square)

    def remove_piece(self, square: int):
        """
        Removes whatever piece is on the square.
        """

        piece = self.squares[square]

        if piece == Piece.EMPTY:
            return Piece.EMPTY

        self.squares[square] = Piece.EMPTY

        self._clear_piece_bit(piece, square)

        self._clear_occupancy(piece, square)

        return piece

    def move_piece(self, from_square: int, to_square: int):
        """
        Moves one piece.

        Captures are handled automatically if
        destination square is occupied.

        Returns captured piece.
        """

        moving_piece = self.squares[from_square]

        if moving_piece == Piece.EMPTY:
            raise ValueError(
                f"No piece on square {from_square}"
            )



        # -------------------------
        # Mailbox
        # -------------------------

        self.squares[from_square] = Piece.EMPTY
        self.squares[to_square] = moving_piece

        # -------------------------
        # Piece Bitboard
        # -------------------------

        bb = self.bitboards[moving_piece]

        bb = clear_bit(bb, from_square)

        bb = set_bit(bb, to_square)

        self.bitboards[moving_piece] = bb

        # -------------------------
        # Occupancy
        # -------------------------

        if is_white(moving_piece):

            self.white_occ = clear_bit(
                self.white_occ,
                from_square
            )

            self.white_occ = set_bit(
                self.white_occ,
                to_square
            )

        else:

            self.black_occ = clear_bit(
                self.black_occ,
                from_square
            )

            self.black_occ = set_bit(
                self.black_occ,
                to_square
            )

        self.all_occ = clear_bit(
            self.all_occ,
            from_square
        )

        self.all_occ = set_bit(
            self.all_occ,
            to_square
        )


    # =====================================================
    # Occupancy Accessors
    # =====================================================

    def white_occupancy(self):
        return self.white_occ

    def black_occupancy(self):
        return self.black_occ

    def occupancy(self):
        return self.all_occ

    # =====================================================
    # Validation
    # =====================================================

    def validate(self):
        """
        Validates that all board representations
        are synchronized.

        Returns
        -------
        bool
            True if valid.

        Raises
        ------
        AssertionError
            If an inconsistency is found.
        """

        # ----------------------------------------
        # Rebuild occupancies from piece bitboards
        # ----------------------------------------

        white = 0
        black = 0

        for piece in range(
            Piece.WHITE_PAWN,
            Piece.WHITE_KING + 1
        ):
            white |= self.bitboards[piece]

        for piece in range(
            Piece.BLACK_PAWN,
            Piece.BLACK_KING + 1
        ):
            black |= self.bitboards[piece]

        all_occ = white | black

        assert white == self.white_occ, \
            "White occupancy mismatch."

        assert black == self.black_occ, \
            "Black occupancy mismatch."

        assert all_occ == self.all_occ, \
            "All occupancy mismatch."

        # ----------------------------------------
        # Mailbox ↔ Bitboards consistency
        # ----------------------------------------

        for square in range(64):

            piece = self.squares[square]

            if piece == Piece.EMPTY:

                assert not get_bit(
                    self.all_occ,
                    square
                ), (
                    f"Square {square} is empty "
                    "but occupancy bit is set."
                )

            else:

                assert get_bit(
                    self.bitboards[piece],
                    square
                ), (
                    f"Piece bitboard missing "
                    f"piece at square {square}"
                )

        return True

    # =====================================================
    # Equality
    # =====================================================

    def __eq__(self, other):

        if not isinstance(other, Board):
            return False

        return (
            self.squares == other.squares
            and self.bitboards == other.bitboards
            and self.white_occ == other.white_occ
            and self.black_occ == other.black_occ
            and self.all_occ == other.all_occ
        )

    # =====================================================
    # Debug Printing
    # =====================================================

    def print_board(self):

        print()

        for rank in range(7, -1, -1):

            print(rank + 1, end=" ")

            for file in range(8):

                square = rank * 8 + file

                piece = self.squares[square]

                print(
                    PIECE_TO_CHAR[piece],
                    end=" "
                )

            print()

        print("  a b c d e f g h")

    # =====================================================
    # Bitboard Debug
    # =====================================================

    def print_bitboards(self):

        print("\n========== BITBOARDS ==========\n")

        names = [
            "",
            "White Pawn",
            "White Knight",
            "White Bishop",
            "White Rook",
            "White Queen",
            "White King",
            "Black Pawn",
            "Black Knight",
            "Black Bishop",
            "Black Rook",
            "Black Queen",
            "Black King",
        ]

        for piece in range(1, 13):

            print(names[piece])

            print_bitboard(
                self.bitboards[piece]
            )

            print()

    # =====================================================
    # String Representation
    # =====================================================

    def __str__(self):

        rows = []

        for rank in range(7, -1, -1):

            row = []

            for file in range(8):

                square = rank * 8 + file

                row.append(
                    PIECE_TO_CHAR[
                        self.squares[square]
                    ]
                )

            rows.append(" ".join(row))

        return "\n".join(rows)
    # =====================================================
# Bitboard Accessors
# =====================================================

    def bitboard(self, piece):

        return self.bitboards[piece]


    def white_pawns(self):

        return self.bitboards[Piece.WHITE_PAWN]


    def white_knights(self):

        return self.bitboards[Piece.WHITE_KNIGHT]


    def white_bishops(self):

        return self.bitboards[Piece.WHITE_BISHOP]


    def white_rooks(self):

        return self.bitboards[Piece.WHITE_ROOK]


    def white_queens(self):

        return self.bitboards[Piece.WHITE_QUEEN]


    def white_king(self):

        return self.bitboards[Piece.WHITE_KING]


    def black_pawns(self):

        return self.bitboards[Piece.BLACK_PAWN]


    def black_knights(self):

        return self.bitboards[Piece.BLACK_KNIGHT]


    def black_bishops(self):

        return self.bitboards[Piece.BLACK_BISHOP]


    def black_rooks(self):

        return self.bitboards[Piece.BLACK_ROOK]


    def black_queens(self):

        return self.bitboards[Piece.BLACK_QUEEN]


    def black_king(self):

        return self.bitboards[Piece.BLACK_KING]


    def white_pieces(self):

        return self.white_occ


    def black_pieces(self):

        return self.black_occ


    def occupied_squares(self):

        return self.all_occ