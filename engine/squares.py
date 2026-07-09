"""
squares.py

Square constants and helper functions.

Board indexing used throughout the engine:

8 | 56 57 58 59 60 61 62 63
7 | 48 49 50 51 52 53 54 55
6 | 40 41 42 43 44 45 46 47
5 | 32 33 34 35 36 37 38 39
4 | 24 25 26 27 28 29 30 31
3 | 16 17 18 19 20 21 22 23
2 |  8  9 10 11 12 13 14 15
1 |  0  1  2  3  4  5  6  7
    a  b  c  d  e  f  g  h
"""

# ==========================================================
# Square Constants
# ==========================================================

A1, B1, C1, D1, E1, F1, G1, H1 = range(0, 8)
A2, B2, C2, D2, E2, F2, G2, H2 = range(8, 16)
A3, B3, C3, D3, E3, F3, G3, H3 = range(16, 24)
A4, B4, C4, D4, E4, F4, G4, H4 = range(24, 32)
A5, B5, C5, D5, E5, F5, G5, H5 = range(32, 40)
A6, B6, C6, D6, E6, F6, G6, H6 = range(40, 48)
A7, B7, C7, D7, E7, F7, G7, H7 = range(48, 56)
A8, B8, C8, D8, E8, F8, G8, H8 = range(56, 64)

NO_SQUARE = -1

FILES = "abcdefgh"
RANKS = "12345678"

# ==========================================================
# Conversion
# ==========================================================

def file_of(square: int) -> int:
    """Returns file (0-7)."""
    return square % 8


def rank_of(square: int) -> int:
    """Returns rank (0-7)."""
    return square // 8


def make_square(file: int, rank: int) -> int:
    """Creates a square from file/rank."""
    return rank * 8 + file


def square_to_string(square: int) -> str:
    """
    Example:
        0  -> a1
        63 -> h8
    """

    if square == NO_SQUARE:
        return "-"

    file = file_of(square)
    rank = rank_of(square)

    return FILES[file] + str(rank + 1)


def square_from_string(square: str) -> int:
    """
    Example:
        e4 -> 28
        a1 -> 0
    """

    if square == "-":
        return NO_SQUARE

    if len(square) != 2:
        raise ValueError(f"Invalid square: {square}")

    file = FILES.index(square[0].lower())
    rank = int(square[1]) - 1

    return make_square(file, rank)

# ==========================================================
# Validation
# ==========================================================

def valid_square(square: int) -> bool:
    """Returns True if square is between A1 and H8."""
    return 0 <= square < 64


def same_rank(sq1: int, sq2: int) -> bool:
    return rank_of(sq1) == rank_of(sq2)


def same_file(sq1: int, sq2: int) -> bool:
    return file_of(sq1) == file_of(sq2)

# ==========================================================
# Distance
# ==========================================================

def manhattan_distance(sq1: int, sq2: int) -> int:
    """
    Manhattan distance between two squares.
    """

    return (
        abs(file_of(sq1) - file_of(sq2))
        +
        abs(rank_of(sq1) - rank_of(sq2))
    )


def chebyshev_distance(sq1: int, sq2: int) -> int:
    """
    King distance between two squares.
    """

    return max(
        abs(file_of(sq1) - file_of(sq2)),
        abs(rank_of(sq1) - rank_of(sq2))
    )

# ==========================================================
# Debug
# ==========================================================

def print_square(square: int):

    print(square_to_string(square))


def print_coordinates(square: int):

    print(
        f"{square_to_string(square)} "
        f"(index={square}, "
        f"file={file_of(square)}, "
        f"rank={rank_of(square)})"
    )