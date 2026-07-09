# from engine.position import Position
# from engine.pieces import Piece
# from engine.position import *
# from engine.fen import (
#     load_start_position,
#     position_to_fen,
#     verify_round_trip,
# )

# position = Position()

# load_start_position(position)

# # position.print()

# # print()

# # print(position_to_fen(position))

# # verify_round_trip(
# #     position_to_fen(position)
# # )

# # print("\nRound-trip verification passed.")
# # from engine.undo import UndoState

# # undo = UndoState()

# # print(undo)
# # from engine.move import *

# # print(bin(CAPTURE))
# # print(bin(PROMOTION))
# # print(bin(CAPTURE | PROMOTION))
# move = encode_move(
#     from_square=12,
#     to_square=28,
#     moving_piece=Piece.WHITE_PAWN,
# )

# position.make_move(move)

# position.print()

"""
main.py

Stage 1 testing.
"""
from copy import deepcopy

from pyautogui import position

from engine.position import Position
from engine.fen import load_fen
from engine.move import *
from engine.squares import square_from_string
from engine.pieces import Piece
from engine.validator import validate_position
from engine.zobrist import (
    initialize_zobrist,
    compute_hash,
)

# ---------------------------------------------------------
# Initialize
# ---------------------------------------------------------

initialize_zobrist()

START_FEN = (
    "rnbqkbnr/"
    "pppppppp/"
    "8/"
    "8/"
    "8/"
    "8/"
    "PPPPPPPP/"
    "RNBQKBNR "
    "w KQkq - 0 1"
)


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def run_test(name, fen, move):

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    position = Position()

    load_fen(position, fen)

    original = deepcopy(position)

    original_hash = compute_hash(original)

    print("\nOriginal Position\n")
    position.print()

    print("\nMaking move...")
    print(move_to_string(move))

    try:
       

        print("\n========== BEFORE MAKE_MOVE ==========")
        print(f"Stored Hash   : 0x{position.hash_key:016X}")
        print(f"Computed Hash : 0x{compute_hash(position):016X}")
        print("======================================\n")   
        position.make_move(move)

        print("\nAfter make_move()\n")
        position.print()

        validate_position(position)

        print("\nUnmaking move...")

        position.unmake_move()

        print("\nAfter unmake_move()\n")
        position.print()

        validate_position(position)

        assert compute_hash(position) == original_hash

        assert position == original

        print("\nPASS")

    except Exception as e:

        print("\nFAILED")

        print(type(e).__name__)

        print(e)


# ---------------------------------------------------------
# Quiet Move
# ---------------------------------------------------------

run_test(
    "Quiet Move",
    START_FEN,
    encode_move(
        square_from_string("e2"),
        square_from_string("e4"),
        Piece.WHITE_PAWN,
    ),
)

# ---------------------------------------------------------
# Pawn Double Push
# ---------------------------------------------------------

run_test(
    "Double Push",
    START_FEN,
    encode_move(
        square_from_string("d2"),
        square_from_string("d4"),
        Piece.WHITE_PAWN,
        flags=DOUBLE_PAWN_PUSH,
    ),
)

# ---------------------------------------------------------
# Normal Capture
# ---------------------------------------------------------

run_test(
    "Capture",
    "4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1",
    encode_move(
        square_from_string("e4"),
        square_from_string("d5"),
        Piece.WHITE_PAWN,
        Piece.BLACK_PAWN,
        flags=CAPTURE,
    ),
)

# ---------------------------------------------------------
# Promotion
# ---------------------------------------------------------

run_test(
    "Promotion",
    "8/P7/8/8/8/8/8/k6K w - - 0 1",
    encode_move(
        square_from_string("a7"),
        square_from_string("a8"),
        Piece.WHITE_PAWN,
        Piece.EMPTY,
        Piece.WHITE_QUEEN,
        PROMOTION,
    ),
)

# ---------------------------------------------------------
# Kingside Castle
# ---------------------------------------------------------

run_test(
    "Kingside Castle",
    "4k2r/8/8/8/8/8/8/4K2R w Kk - 0 1",
    encode_move(
        square_from_string("e1"),
        square_from_string("g1"),
        Piece.WHITE_KING,
        flags=KING_CASTLE,
    ),
)

# ---------------------------------------------------------
# Queenside Castle
# ---------------------------------------------------------

run_test(
    "Queenside Castle",
    "r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 1",
    encode_move(
        square_from_string("e1"),
        square_from_string("c1"),
        Piece.WHITE_KING,
        flags=QUEEN_CASTLE,
    ),
)

# ---------------------------------------------------------
# En Passant
# ---------------------------------------------------------

run_test(
    "En Passant",
    "8/8/8/3pP3/8/8/8/k6K w - d6 0 1",
    encode_move(
        square_from_string("e5"),
        square_from_string("d6"),
        Piece.WHITE_PAWN,
        Piece.BLACK_PAWN,
        flags=EN_PASSANT | CAPTURE,
    ),
)

print("\n")
print("=" * 60)
print("ALL TESTS FINISHED")
print("=" * 60)