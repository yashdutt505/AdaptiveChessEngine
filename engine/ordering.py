"""Stateful killer and history heuristics for search move ordering."""

from .move import from_square, is_capture, is_promotion, to_square


MAX_ORDERING_PLY = 128
MAX_HISTORY_SCORE = 1_000_000


class SearchHeuristics:
    def __init__(self):
        self.killers = [[None, None] for _ in range(MAX_ORDERING_PLY)]
        self.history = [
            [[0 for _ in range(64)] for _ in range(64)]
            for _ in range(2)
        ]
        self.beta_cutoffs = 0
        self.first_move_cutoffs = 0
        self.countermoves = [[None for _ in range(64)] for _ in range(64)]

    def record_cutoff(
        self, move, depth, ply, color, move_index,
        previous_move=None, tried_quiets=(),
    ):
        self.beta_cutoffs += 1
        if move_index == 0:
            self.first_move_cutoffs += 1
        if is_capture(move) or is_promotion(move):
            return

        if ply < MAX_ORDERING_PLY:
            first, _ = self.killers[ply]
            if move != first:
                self.killers[ply] = [move, first]

        frm = from_square(move)
        to = to_square(move)
        bonus = max(depth, 1) ** 2
        self.history[color][frm][to] = min(
            self.history[color][frm][to] + bonus,
            MAX_HISTORY_SCORE,
        )
        if previous_move is not None:
            self.countermoves[from_square(previous_move)][to_square(previous_move)] = move

        malus = max(depth, 1) ** 2
        for failed in tried_quiets:
            if is_capture(failed) or is_promotion(failed):
                continue
            failed_from = from_square(failed)
            failed_to = to_square(failed)
            self.history[color][failed_from][failed_to] = max(
                -MAX_HISTORY_SCORE,
                self.history[color][failed_from][failed_to] - malus,
            )

    def killer_rank(self, move, ply):
        if ply >= MAX_ORDERING_PLY:
            return 0
        if move == self.killers[ply][0]:
            return 2
        if move == self.killers[ply][1]:
            return 1
        return 0

    def history_score(self, move, color):
        return self.history[color][from_square(move)][to_square(move)]

    def is_countermove(self, move, previous_move):
        if previous_move is None:
            return False
        return self.countermoves[
            from_square(previous_move)
        ][to_square(previous_move)] == move

    def age_history(self):
        for color in range(2):
            for frm in range(64):
                for to in range(64):
                    self.history[color][frm][to] //= 2
