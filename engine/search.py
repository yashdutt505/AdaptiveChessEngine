"""Fixed-depth negamax search with alpha-beta pruning and quiescence."""

from dataclasses import dataclass, field

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


class Searcher:
    def __init__(self):
        self.nodes = 0

    def search(self, position, depth):
        if depth < 1:
            raise ValueError("Search depth must be at least one")
        self.nodes = 0
        legal_moves = generate_legal_moves(position)
        if legal_moves and is_rule_draw(position):
            best_move = self._ordered_moves(legal_moves)[0]
            return SearchResult(best_move, 0, depth, 1, [best_move])
        score, pv = self._negamax(position, depth, -INFINITY, INFINITY, 0)
        return SearchResult(
            best_move=pv[0] if pv else None,
            score=score,
            depth=depth,
            nodes=self.nodes,
            pv=pv,
        )

    def _negamax(self, position, depth, alpha, beta, ply):
        self.nodes += 1
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
            child_score, child_line = self._negamax(
                position, depth - 1, -beta, -alpha, ply + 1
            )
            score = -child_score
            position.unmake_move()

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
            score = -self._quiescence(position, -beta, -alpha, ply + 1)
            position.unmake_move()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    @staticmethod
    def _ordered_moves(moves):
        def score(move):
            capture = PIECE_VALUES.get(captured_piece(move), 0)
            promotion = PIECE_VALUES.get(promotion_piece(move), 0)
            return promotion * 10 + capture * 10 - (move >> 12 & 0xF)

        return sorted(moves, key=score, reverse=True)
