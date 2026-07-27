"""Fixed-depth negamax search with alpha-beta pruning and quiescence."""

from dataclasses import dataclass, field
import threading
import time

from .attacks import is_in_check
from .evaluation import PIECE_VALUES, evaluate
from .game import is_rule_draw
from .move import captured_piece, is_capture, is_promotion, promotion_piece
from .movegen import generate_legal_moves


INFINITY = 1_000_000
MATE_SCORE = 100_000
MAX_PLY = 128


@dataclass(slots=True)
class SearchResult:
    best_move: int | None
    score: int
    depth: int
    nodes: int
    pv: list[int] = field(default_factory=list)
    time_ms: int = 0


class SearchStopped(Exception):
    pass


class Searcher:
    def __init__(self, stop_event=None, deadline=None, preferred_move=None):
        self.nodes = 0
        self.stop_event = stop_event or threading.Event()
        self.deadline = deadline
        self.preferred_move = preferred_move
        self.started_at = 0.0

    def search(self, position, depth):
        if depth < 1:
            raise ValueError("Search depth must be at least one")
        self.nodes = 0
        self.started_at = time.monotonic()
        self._check_stop()
        legal_moves = generate_legal_moves(position)
        if legal_moves and is_rule_draw(position):
            best_move = self._ordered_moves(legal_moves)[0]
            return SearchResult(best_move, 0, depth, 1, [best_move], self._elapsed_ms())
        score, pv = self._negamax(position, depth, -INFINITY, INFINITY, 0)
        return SearchResult(
            best_move=pv[0] if pv else None,
            score=score,
            depth=depth,
            nodes=self.nodes,
            pv=pv,
            time_ms=self._elapsed_ms(),
        )

    def _negamax(self, position, depth, alpha, beta, ply):
        self.nodes += 1
        self._check_stop()
        legal_moves = generate_legal_moves(position)
        if not legal_moves:
            if is_in_check(position):
                return -MATE_SCORE + ply, []
            return 0, []
        if is_rule_draw(position):
            return 0, []
        if depth == 0:
            return self._quiescence(position, alpha, beta, ply), []

        best_score = -INFINITY
        best_line = []
        for move in self._ordered_moves(legal_moves):
            position.make_move(move)
            try:
                child_score, child_line = self._negamax(
                    position, depth - 1, -beta, -alpha, ply + 1
                )
            finally:
                position.unmake_move()
            score = -child_score

            if score > best_score:
                best_score = score
                best_line = [move, *child_line]
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best_score, best_line

    def _quiescence(self, position, alpha, beta, ply):
        self.nodes += 1
        self._check_stop()
        if ply >= MAX_PLY:
            return evaluate(position)
        if is_rule_draw(position):
            return 0

        in_check = is_in_check(position)
        legal_moves = generate_legal_moves(position)
        if not legal_moves:
            return -MATE_SCORE + ply if in_check else 0

        if not in_check:
            stand_pat = evaluate(position)
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat
            legal_moves = [
                move for move in legal_moves
                if is_capture(move) or is_promotion(move)
            ]

        for move in self._ordered_moves(legal_moves):
            position.make_move(move)
            try:
                score = -self._quiescence(position, -beta, -alpha, ply + 1)
            finally:
                position.unmake_move()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def _ordered_moves(self, moves):
        def score(move):
            capture = PIECE_VALUES.get(captured_piece(move), 0)
            promotion = PIECE_VALUES.get(promotion_piece(move), 0)
            preferred = 1_000_000 if move == self.preferred_move else 0
            return preferred + promotion * 10 + capture * 10 - (move >> 12 & 0xF)

        return sorted(moves, key=score, reverse=True)

    def _check_stop(self):
        if self.stop_event.is_set():
            raise SearchStopped
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self.stop_event.set()
            raise SearchStopped

    def _elapsed_ms(self):
        return max(0, int((time.monotonic() - self.started_at) * 1000))


def iterative_deepening(
    position,
    max_depth=64,
    time_limit_ms=None,
    stop_event=None,
    info_callback=None,
):
    """Search increasing depths and return the last fully completed result."""
    if max_depth < 1:
        raise ValueError("Maximum depth must be at least one")
    stop_event = stop_event or threading.Event()
    started = time.monotonic()
    deadline = (
        started + time_limit_ms / 1000
        if time_limit_ms is not None
        else None
    )
    best = None
    preferred_move = None
    total_nodes = 0

    for depth in range(1, max_depth + 1):
        searcher = Searcher(stop_event, deadline, preferred_move)
        try:
            result = searcher.search(position, depth)
        except SearchStopped:
            break
        total_nodes += result.nodes
        result.nodes = total_nodes
        result.time_ms = int((time.monotonic() - started) * 1000)
        best = result
        preferred_move = result.best_move
        if info_callback is not None:
            info_callback(result)
        if abs(result.score) >= MATE_SCORE - depth:
            break

    if best is None:
        legal = generate_legal_moves(position)
        best_move = legal[0] if legal else None
        best = SearchResult(
            best_move=best_move,
            score=0,
            depth=0,
            nodes=total_nodes,
            pv=[best_move] if best_move is not None else [],
            time_ms=int((time.monotonic() - started) * 1000),
        )
    return best
