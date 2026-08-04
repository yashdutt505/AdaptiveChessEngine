"""EPD best-move test runner with deterministic node budgets."""

from dataclasses import dataclass

from .fen import load_fen
from .move import move_to_string
from .position import Position
from .search import iterative_deepening
from .transposition import TranspositionTable


@dataclass(frozen=True, slots=True)
class EPDCase:
    fen: str
    best_moves: frozenset[str]
    name: str = ""


def parse_epd_line(line):
    """Parse the common four-field EPD form with bm and optional id."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    segments = [segment.strip() for segment in text.split(";") if segment.strip()]
    head = segments[0].split()
    if len(head) < 6 or "bm" not in head:
        raise ValueError("EPD line requires four position fields and a bm operation")
    bm_index = head.index("bm")
    fen = " ".join(head[:4]) + " 0 1"
    best_moves = frozenset(head[bm_index + 1 :])
    if not best_moves:
        raise ValueError("EPD bm operation requires at least one move")
    name = ""
    for segment in segments[1:]:
        if segment.startswith("id "):
            name = segment[3:].strip().strip('"')
    return EPDCase(fen, best_moves, name)


def run_epd_cases(cases, nodes_per_case=10_000):
    results = []
    for case in cases:
        position = Position()
        load_fen(position, case.fen)
        result = iterative_deepening(
            position,
            node_limit=nodes_per_case,
            transposition_table=TranspositionTable(16),
        )
        move = move_to_string(result.best_move) if result.best_move is not None else "0000"
        results.append({
            "name": case.name,
            "move": move,
            "expected": case.best_moves,
            "passed": move in case.best_moves,
            "nodes": result.nodes,
            "depth": result.depth,
        })
    return results
