"""Small deterministic tactical benchmark for development regressions."""

from dataclasses import dataclass
import time

from .fen import load_fen
from .move import move_to_string
from .position import Position
from .search import Searcher
from .transposition import TranspositionTable


@dataclass(frozen=True, slots=True)
class TacticalCase:
    name: str
    fen: str
    expected_moves: frozenset[str]


TACTICAL_CASES = (
    TacticalCase(
        "White mate in one",
        "7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - 0 1",
        frozenset({"d1d8"}),
    ),
    TacticalCase(
        "Black mate in one",
        "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2",
        frozenset({"d8h4"}),
    ),
    TacticalCase(
        "Win hanging queen",
        "q6k/8/8/8/8/8/8/R5K1 w - - 0 1",
        frozenset({"a1a8"}),
    ),
    TacticalCase(
        "Back-rank mate",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
        frozenset({"d1d8"}),
    ),
)


def run_tactical_benchmark(depth=3):
    results = []
    for case in TACTICAL_CASES:
        position = Position()
        load_fen(position, case.fen)
        started = time.monotonic()
        result = Searcher(
            transposition_table=TranspositionTable(4)
        ).search(position, depth)
        move = move_to_string(result.best_move) if result.best_move is not None else "0000"
        results.append({
            "name": case.name,
            "move": move,
            "passed": move in case.expected_moves,
            "nodes": result.nodes,
            "time_ms": int((time.monotonic() - started) * 1000),
            "depth": depth,
        })
    return results
