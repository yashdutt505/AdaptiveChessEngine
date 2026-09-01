"""Run a legal, color-swapped UCI gauntlet and estimate Elo from the score."""

import argparse
import json
import math
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.attacks import is_in_check
from engine.constants import START_FEN
from engine.fen import load_fen
from engine.game import is_rule_draw
from engine.move import move_to_string
from engine.movegen import generate_legal_moves
from engine.position import Position


OPENINGS = (
    ("e2e4", "e7e5", "g1f3", "b8c6"),
    ("d2d4", "d7d5", "c2c4", "e7e6"),
    ("e2e4", "c7c5", "g1f3", "d7d6"),
    ("g1f3", "d7d5", "d2d4", "g8f6"),
    ("c2c4", "e7e5", "b1c3", "g8f6"),
    ("e2e4", "e7e6", "d2d4", "d7d5"),
    ("d2d4", "g8f6", "c2c4", "g7g6"),
    ("e2e4", "c7c6", "d2d4", "d7d5"),
)


def parse_uci_options(items):
    options = []
    for item in items:
        if "=" not in item:
            raise ValueError("target option must use NAME=VALUE")
        name, value = item.split("=", 1)
        if not name.strip() or not value.strip():
            raise ValueError("target option requires a non-empty name and value")
        options.append((name.strip(), value.strip()))
    return options


class UCIEngine:
    def __init__(self, path, options=()):
        self.path = str(Path(path).resolve())
        self.process = subprocess.Popen(
            [self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        self.lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self.send("uci")
        self.wait_for("uciok", 10)
        for name, value in options:
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.wait_for("readyok", 10)

    def _read(self):
        for line in self.process.stdout:
            self.lines.put(line.strip())

    def send(self, command):
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def wait_for(self, prefix, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if line.startswith(prefix):
                return line
        raise TimeoutError(f"{Path(self.path).name} did not return {prefix}")

    def move(self, moves, movetime):
        suffix = " moves " + " ".join(moves) if moves else ""
        self.send("position startpos" + suffix)
        self.send(f"go movetime {movetime}")
        line = self.wait_for("bestmove ", max(10, movetime / 1000 * 10))
        return line.split()[1]

    def new_game(self):
        self.send("ucinewgame")
        self.send("isready")
        self.wait_for("readyok", 10)

    def close(self):
        if self.process.poll() is None:
            self.send("quit")
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()


def legal_move(position, text):
    for move in generate_legal_moves(position):
        if move_to_string(move) == text:
            return move
    return None


def play(target, reference, target_white, opening, movetime, max_plies):
    position = Position()
    load_fen(position, START_FEN)
    moves = []
    for text in opening:
        move = legal_move(position, text)
        if move is None:
            raise ValueError(f"bad opening move {text}")
        position.make_move(move)
        moves.append(text)
    target.new_game()
    reference.new_game()
    for _ in range(len(moves), max_plies):
        legal = generate_legal_moves(position)
        if not legal:
            if is_in_check(position, position.side_to_move):
                white_result = -1 if position.side_to_move == 0 else 1
            else:
                white_result = 0
            return (white_result if target_white else -white_result), moves, "terminal"
        if is_rule_draw(position):
            return 0, moves, "rule-draw"
        target_turn = (position.side_to_move == 0) == target_white
        engine = target if target_turn else reference
        try:
            text = engine.move(moves, movetime)
        except (TimeoutError, BrokenPipeError):
            return (-1 if target_turn else 1), moves, "timeout-or-crash"
        move = legal_move(position, text)
        if move is None:
            return (-1 if target_turn else 1), moves, f"illegal:{text}"
        position.make_move(move)
        moves.append(text)
    return 0, moves, "max-plies"


def estimate_elo(opponent_elo, scores):
    mean = sum(scores) / len(scores)
    if mean <= 0 or mean >= 1:
        return mean, None, None
    variance = sum((score - mean) ** 2 for score in scores) / max(1, len(scores) - 1)
    standard_error = math.sqrt(variance / len(scores))
    low = max(0.001, mean - 1.96 * standard_error)
    high = min(0.999, mean + 1.96 * standard_error)
    convert = lambda score: opponent_elo + 400 * math.log10(score / (1 - score))
    return mean, convert(mean), (convert(low), convert(high))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--opponent-elo", type=int, required=True)
    parser.add_argument("--games", type=int, default=32)
    parser.add_argument("--movetime", type=int, default=50)
    parser.add_argument("--max-plies", type=int, default=160)
    parser.add_argument(
        "--target-option", action="append", default=[], metavar="NAME=VALUE",
        help="repeatable UCI option applied to the target engine",
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        target_options = [("Hash", 64), *parse_uci_options(args.target_option)]
    except ValueError as error:
        parser.error(str(error))
    target = UCIEngine(args.target, target_options)
    reference = UCIEngine(args.reference, (("Threads", 1), ("Hash", 64), ("UCI_LimitStrength", "true"), ("UCI_Elo", args.opponent_elo)))
    records = []
    try:
        for game in range(args.games):
            opening = OPENINGS[(game // 2) % len(OPENINGS)]
            target_white = game % 2 == 0
            result, moves, reason = play(target, reference, target_white, opening, args.movetime, args.max_plies)
            score = 1.0 if result > 0 else 0.0 if result < 0 else 0.5
            records.append({"game": game + 1, "target_white": target_white, "score": score, "reason": reason, "moves": moves})
            print(f"game {game + 1}/{args.games}: score={score} plies={len(moves)} reason={reason}", flush=True)
    finally:
        target.close()
        reference.close()
    score, estimate, interval = estimate_elo(args.opponent_elo, [record["score"] for record in records])
    summary = {"opponent_elo": args.opponent_elo, "games": len(records), "target_options": target_options, "score": score, "estimated_elo": estimate, "approx_95_interval": interval, "records": records}
    print(json.dumps({key: value for key, value in summary.items() if key != "records"}, indent=2))
    if args.output:
        path = Path(args.output);path.parent.mkdir(parents=True, exist_ok=True);path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
