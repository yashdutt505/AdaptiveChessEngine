"""Fixed-depth negamax search with alpha-beta pruning and quiescence."""

from dataclasses import dataclass, field
import threading
import time

from .attacks import is_in_check
from .evaluation import PIECE_VALUES, evaluate
from .game import is_rule_draw
from .move import (
    captured_piece,
    is_capture,
    is_promotion,
    moving_piece,
    promotion_piece,
)
from .movegen import generate_legal_moves
from .ordering import SearchHeuristics
from .transposition import EXACT, LOWER_BOUND, UPPER_BOUND


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
    beta_cutoffs: int = 0
    first_move_cutoffs: int = 0


class SearchStopped(Exception):
    pass


class Searcher:
    def __init__(
        self,
        stop_event=None,
        deadline=None,
        preferred_move=None,
        transposition_table=None,
        heuristics=None,
        enable_heuristics=True,
    ):
        self.nodes = 0
        self.stop_event = stop_event or threading.Event()
        self.deadline = deadline
        self.preferred_move = preferred_move
        self.transposition_table = transposition_table
        self.enable_heuristics = enable_heuristics
        self.heuristics = heuristics or SearchHeuristics()
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
            return SearchResult(
                best_move, 0, depth, 1, [best_move], self._elapsed_ms(),
                self.heuristics.beta_cutoffs,
                self.heuristics.first_move_cutoffs,
            )
        score, pv = self._negamax(position, depth, -INFINITY, INFINITY, 0)
        return SearchResult(
            best_move=pv[0] if pv else None,
            score=score,
            depth=depth,
            nodes=self.nodes,
            pv=pv,
            time_ms=self._elapsed_ms(),
            beta_cutoffs=self.heuristics.beta_cutoffs,
            first_move_cutoffs=self.heuristics.first_move_cutoffs,
        )

    def _negamax(self, position, depth, alpha, beta, ply):
        self.nodes += 1
        self._check_stop()
        if is_rule_draw(position):
            return 0, []
        if depth == 0:
            return self._quiescence(position, alpha, beta, ply), []

        original_alpha = alpha
        tt_move = None
        if self.transposition_table is not None:
            entry = self.transposition_table.probe(position.hash_key)
            if entry is not None:
                tt_move = entry.best_move
                if entry.depth >= depth:
                    score = self._score_from_tt(entry.score, ply)
                    if entry.flag == EXACT:
                        return score, [tt_move] if tt_move is not None else []
                    if entry.flag == LOWER_BOUND:
                        alpha = max(alpha, score)
                    elif entry.flag == UPPER_BOUND:
                        beta = min(beta, score)
                    if alpha >= beta:
                        return score, [tt_move] if tt_move is not None else []

        legal_moves = generate_legal_moves(position)
        if not legal_moves:
            score = -MATE_SCORE + ply if is_in_check(position) else 0
            self._store_tt(position, depth, score, EXACT, None, ply)
            return score, []

        best_score = -INFINITY
        best_line = []
        color = position.side_to_move
        for move_index, move in enumerate(
            self._ordered_moves(legal_moves, tt_move, ply, color)
        ):
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
                if self.enable_heuristics:
                    self.heuristics.record_cutoff(
                        move, depth, ply, color, move_index
                    )
                break
        flag = EXACT
        if best_score <= original_alpha:
            flag = UPPER_BOUND
        elif best_score >= beta:
            flag = LOWER_BOUND
        self._store_tt(
            position, depth, best_score, flag,
            best_line[0] if best_line else None, ply,
        )
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

        for move in self._ordered_moves(
            legal_moves, ply=ply, color=position.side_to_move
        ):
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

    def _ordered_moves(self, moves, tt_move=None, ply=0, color=0):
        def score(move):
            capture = PIECE_VALUES.get(captured_piece(move), 0)
            promotion = PIECE_VALUES.get(promotion_piece(move), 0)
            attacker = PIECE_VALUES.get(moving_piece(move), 0)
            hash_bonus = 2_000_000 if move == tt_move else 0
            preferred = 1_000_000 if move == self.preferred_move else 0
            if is_promotion(move):
                tactical = 800_000 + promotion
            elif is_capture(move):
                tactical = 700_000 + capture * 16 - attacker
            else:
                tactical = 0
            heuristic = 0
            if self.enable_heuristics and tactical == 0:
                killer_rank = self.heuristics.killer_rank(move, ply)
                heuristic = (
                    killer_rank * 100_000
                    + self.heuristics.history_score(move, color)
                )
            return hash_bonus + preferred + tactical + heuristic

        return sorted(moves, key=score, reverse=True)

    def _check_stop(self):
        if self.stop_event.is_set():
            raise SearchStopped
        if self.deadline is not None and time.monotonic() >= self.deadline:
            self.stop_event.set()
            raise SearchStopped

    def _elapsed_ms(self):
        return max(0, int((time.monotonic() - self.started_at) * 1000))

    def _store_tt(self, position, depth, score, flag, best_move, ply):
        if self.transposition_table is not None:
            self.transposition_table.store(
                position.hash_key,
                depth,
                self._score_to_tt(score, ply),
                flag,
                best_move,
            )

    @staticmethod
    def _score_to_tt(score, ply):
        if score >= MATE_SCORE - MAX_PLY:
            return score + ply
        if score <= -MATE_SCORE + MAX_PLY:
            return score - ply
        return score

    @staticmethod
    def _score_from_tt(score, ply):
        if score >= MATE_SCORE - MAX_PLY:
            return score - ply
        if score <= -MATE_SCORE + MAX_PLY:
            return score + ply
        return score


def iterative_deepening(
    position,
    max_depth=64,
    time_limit_ms=None,
    stop_event=None,
    info_callback=None,
    transposition_table=None,
    enable_heuristics=True,
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
    heuristics = SearchHeuristics()
    if transposition_table is not None:
        transposition_table.new_search()

    for depth in range(1, max_depth + 1):
        searcher = Searcher(
            stop_event,
            deadline,
            preferred_move,
            transposition_table,
            heuristics,
            enable_heuristics,
        )
        try:
            result = searcher.search(position, depth)
        except SearchStopped:
            break
        total_nodes += result.nodes
        result.nodes = total_nodes
        result.time_ms = int((time.monotonic() - started) * 1000)
        result.beta_cutoffs = heuristics.beta_cutoffs
        result.first_move_cutoffs = heuristics.first_move_cutoffs
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
            beta_cutoffs=heuristics.beta_cutoffs,
            first_move_cutoffs=heuristics.first_move_cutoffs,
        )
    return best
