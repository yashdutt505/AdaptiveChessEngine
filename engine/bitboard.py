"""
bitboard.py

Low-level bitboard utilities.

A bitboard is a 64-bit integer where each bit represents
one square on the chess board.

Bit numbering:

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

Bitboard = int

FULL_BOARD = 0xFFFFFFFFFFFFFFFF
EMPTY_BOARD = 0
# ==========================================================
# Basic Bit Operations
# ==========================================================

def bit(square: int) -> Bitboard:
    """
    Returns a bitboard with exactly one bit set.
    """

    return 1 << square


def set_bit(
    bb: Bitboard,
    square: int
) -> Bitboard:

    return bb | bit(square)


def clear_bit(
    bb: Bitboard,
    square: int
) -> Bitboard:

    return bb & ~bit(square)


def toggle_bit(
    bb: Bitboard,
    square: int
) -> Bitboard:

    return bb ^ bit(square)


def get_bit(
    bb: Bitboard,
    square: int
) -> bool:

    return (bb >> square) & 1
# ==========================================================
# Counting Bits
# ==========================================================

def popcount(bb: Bitboard) -> int:
    """
    Returns the number of set bits.
    """

    return bb.bit_count()


def is_empty(bb: Bitboard) -> bool:
    """
    Returns True if no bits are set.
    """

    return bb == EMPTY_BOARD


def has_one_bit(bb: Bitboard) -> bool:
    """
    Returns True if exactly one bit is set.
    """

    return bb != 0 and (bb & (bb - 1)) == 0
# ==========================================================
# Bit Scanning
# ==========================================================

def lsb(bb: Bitboard) -> int:
    """
    Returns the index of the Least Significant Bit.

    Example

    0001001000

    returns

    3
    """

    if bb == 0:
        raise ValueError("Bitboard is empty.")

    return (bb & -bb).bit_length() - 1


def msb(bb: Bitboard) -> int:
    """
    Returns the index of the Most Significant Bit.
    """

    if bb == 0:
        raise ValueError("Bitboard is empty.")

    return bb.bit_length() - 1
# ==========================================================
# Pop Least Significant Bit
# ==========================================================

def pop_lsb(bb: Bitboard):
    """
    Removes the least significant bit.

    Returns

    (
        square,
        new_bitboard
    )
    """

    square = lsb(bb)

    bb &= bb - 1

    return square, bb# ==========================================================
# Bitboard Iteration
# ==========================================================

def bits(bb: Bitboard):
    """
    Iterates over all set bits.

    Example:

        for square in bits(bitboard):
            ...

    Yields squares from least significant
    to most significant.
    """

    while bb:

        square, bb = pop_lsb(bb)

        yield square
# ==========================================================
# Formatting
# ==========================================================

def to_binary(bb: Bitboard) -> str:
    """
    Returns a 64-character binary string.
    """

    return format(bb, "064b")


def to_hex(bb: Bitboard) -> str:
    """
    Returns hexadecimal representation.
    """

    return hex(bb)
# ==========================================================
# Debug Printing
# ==========================================================

def board_string(bb: Bitboard) -> str:
    """
    Returns a printable chessboard
    representation of a bitboard.
    """

    lines = []

    for rank in range(7, -1, -1):

        row = [str(rank + 1)]

        for file in range(8):

            square = rank * 8 + file

            row.append(
                "1" if get_bit(bb, square) else "."
            )

        lines.append(" ".join(row))

    lines.append("  a b c d e f g h")

    return "\n".join(lines)


def print_bitboard(bb: Bitboard):
    """
    Pretty-print a bitboard.
    """

    print(board_string(bb))
# ==========================================================
# Validation
# ==========================================================

def validate_square(square: int):
    """
    Raises if the square is invalid.
    """

    if square < 0 or square >= 64:

        raise ValueError(
            f"Invalid square: {square}"
        )


def validate_bitboard(bb: Bitboard):
    """
    Ensures the value fits within 64 bits.
    """

    if bb < 0:

        raise ValueError(
            "Bitboard cannot be negative."
        )

    if bb > FULL_BOARD:

        raise ValueError(
            "Bitboard exceeds 64 bits."
        )