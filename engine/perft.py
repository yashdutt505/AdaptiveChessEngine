"""Move-generation verification helpers."""

from .move import move_to_string
from .movegen import generate_legal_moves


def perft(position, depth):
    """Count legal leaf nodes at exactly ``depth`` plies."""
    if depth < 0:
        raise ValueError("Perft depth cannot be negative")
    if depth == 0:
        return 1
    moves = generate_legal_moves(position)
    if depth == 1:
        return len(moves)
    nodes = 0
    for move in moves:
        position.make_move(move)
        nodes += perft(position, depth - 1)
        position.unmake_move()
    return nodes


def divide(position, depth):
    """Return the perft count associated with each root move."""
    if depth < 1:
        raise ValueError("Divide depth must be at least one")
    result = {}
    for move in generate_legal_moves(position):
        position.make_move(move)
        result[move_to_string(move)] = perft(position, depth - 1)
        position.unmake_move()
    return result
