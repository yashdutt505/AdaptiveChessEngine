"""Deterministic fixed-node self-play for engine validation and A/B testing."""

from dataclasses import dataclass, field

from .attacks import is_in_check
from .constants import BLACK, START_FEN, WHITE
from .fen import load_fen
from .game import is_rule_draw
from .move import move_to_string
from .movegen import generate_legal_moves
from .position import Position
from .search import iterative_deepening
from .transposition import TranspositionTable


@dataclass(slots=True)
class SelfPlayResult:
    result: str
    reason: str
    moves: list[str] = field(default_factory=list)
    nodes: int = 0


def play_fixed_node_game(nodes_per_move=1_000, max_plies=200, start_fen=START_FEN):
    """Play one deterministic engine-vs-itself game."""
    if nodes_per_move < 1:
        raise ValueError("nodes_per_move must be positive")
    position = Position()
    load_fen(position, start_fen)
    tables = [TranspositionTable(16), TranspositionTable(16)]
    moves = []
    total_nodes = 0

    for _ in range(max_plies):
        legal = generate_legal_moves(position)
        if not legal:
            if is_in_check(position):
                result = "0-1" if position.side_to_move == WHITE else "1-0"
                return SelfPlayResult(result, "checkmate", moves, total_nodes)
            return SelfPlayResult("1/2-1/2", "stalemate", moves, total_nodes)
        if is_rule_draw(position):
            return SelfPlayResult("1/2-1/2", "rule draw", moves, total_nodes)

        result = iterative_deepening(
            position,
            node_limit=nodes_per_move,
            transposition_table=tables[position.side_to_move],
        )
        if result.best_move not in legal:
            raise AssertionError("Self-play search returned an illegal move")
        moves.append(move_to_string(result.best_move))
        total_nodes += result.nodes
        position.make_move(result.best_move)

    return SelfPlayResult("1/2-1/2", "ply limit", moves, total_nodes)
