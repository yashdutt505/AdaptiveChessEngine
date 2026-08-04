"""Universal Chess Interface protocol and asynchronous search control."""

import sys
import threading

from .constants import BLACK, START_FEN, WHITE
from .fen import load_fen
from .move import move_to_string
from .movegen import generate_legal_moves
from .position import Position
from .search import MATE_SCORE, iterative_deepening
from .transposition import TranspositionTable


ENGINE_NAME = "Adaptive Chess Engine"
ENGINE_AUTHOR = "Yash Dutt"


def find_legal_uci_move(position, text):
    text = text.strip().lower()
    for move in generate_legal_moves(position):
        if move_to_string(move) == text:
            return move
    raise ValueError(f"Illegal move: {text}")


class UCIEngine:
    def __init__(self, output=None):
        self.output = output or (lambda line: print(line, flush=True))
        self.position = Position()
        load_fen(self.position, START_FEN)
        self.search_thread = None
        self.stop_event = None
        self._output_lock = threading.Lock()
        self.transposition_table = TranspositionTable(64)
        self.move_overhead_ms = 20

    def send(self, line):
        with self._output_lock:
            self.output(line)

    def handle_line(self, line):
        """Handle one command. Return False when the process should exit."""
        tokens = line.strip().split()
        if not tokens:
            return True
        command = tokens[0].lower()

        if command == "uci":
            self.send(f"id name {ENGINE_NAME}")
            self.send(f"id author {ENGINE_AUTHOR}")
            self.send("option name Hash type spin default 64 min 1 max 1024")
            self.send("option name Clear Hash type button")
            self.send("option name Move Overhead type spin default 20 min 0 max 5000")
            self.send("uciok")
        elif command == "isready":
            self.send("readyok")
        elif command == "ucinewgame":
            self.stop_search()
            load_fen(self.position, START_FEN)
        elif command == "position":
            self.stop_search()
            self._set_position(tokens[1:])
        elif command == "go":
            self._start_search(tokens[1:])
        elif command == "stop":
            self.stop_search()
        elif command == "quit":
            self.stop_search()
            return False
        elif command == "setoption":
            self._set_option(tokens[1:])
        elif command in ("ponderhit", "debug"):
            pass
        return True

    def _set_position(self, tokens):
        if not tokens:
            raise ValueError("position requires startpos or fen")
        if tokens[0] == "startpos":
            load_fen(self.position, START_FEN)
            index = 1
        elif tokens[0] == "fen":
            if len(tokens) < 7:
                raise ValueError("position fen requires six FEN fields")
            load_fen(self.position, " ".join(tokens[1:7]))
            index = 7
        else:
            raise ValueError("position requires startpos or fen")

        if index < len(tokens):
            if tokens[index] != "moves":
                raise ValueError("Expected moves after position")
            for text in tokens[index + 1 :]:
                self.position.make_move(find_legal_uci_move(self.position, text))

    def _start_search(self, tokens):
        self.stop_search()
        options = self._parse_go(tokens)
        self.stop_event = threading.Event()
        self.search_thread = threading.Thread(
            target=self._search_worker,
            args=(options,),
            name="uci-search",
            daemon=True,
        )
        self.search_thread.start()

    def _search_worker(self, options):
        try:
            result = iterative_deepening(
                self.position,
                max_depth=options["depth"],
                time_limit_ms=options["time_limit_ms"],
                stop_event=self.stop_event,
                info_callback=self._send_search_info,
                transposition_table=self.transposition_table,
                node_limit=options["node_limit"],
            )
            move = move_to_string(result.best_move) if result.best_move is not None else "0000"
            self.send(f"bestmove {move}")
        except Exception as error:
            self.send(f"info string search error: {error}")
            self.send("bestmove 0000")

    def _send_search_info(self, result):
        elapsed = max(result.time_ms, 1)
        nps = result.nodes * 1000 // elapsed
        pv = " ".join(move_to_string(move) for move in result.pv)
        if abs(result.score) >= MATE_SCORE - 1000:
            plies = MATE_SCORE - abs(result.score)
            mate = (plies + 1) // 2
            if result.score < 0:
                mate = -mate
            score = f"mate {mate}"
        else:
            score = f"cp {result.score}"
        self.send(
            f"info depth {result.depth} score {score} nodes {result.nodes} "
            f"time {result.time_ms} nps {nps} "
            f"hashfull {self.transposition_table.hashfull()} pv {pv}"
        )

    def _set_option(self, tokens):
        lowered = [token.lower() for token in tokens]
        if not lowered or lowered[0] != "name":
            return
        try:
            value_index = lowered.index("value")
        except ValueError:
            value_index = len(tokens)
        name = " ".join(lowered[1:value_index])
        value = " ".join(tokens[value_index + 1 :])
        if name == "hash" and value:
            size_mb = max(1, min(int(value), 1024))
            self.stop_search()
            self.transposition_table.resize(size_mb)
        elif name == "clear hash":
            self.stop_search()
            self.transposition_table.clear()
        elif name == "move overhead" and value:
            self.move_overhead_ms = max(0, min(int(value), 5000))

    def _parse_go(self, tokens):
        values = {}
        flags = {"infinite", "ponder"}
        numeric = {
            "depth", "movetime", "wtime", "btime",
            "winc", "binc", "movestogo",
            "nodes", "mate",
        }
        index = 0
        while index < len(tokens):
            name = tokens[index]
            if name in flags:
                values[name] = True
                index += 1
            elif name in numeric and index + 1 < len(tokens):
                values[name] = max(0, int(tokens[index + 1]))
                index += 2
            else:
                index += 1

        depth = values.get("depth", 64)
        if "mate" in values:
            depth = min(depth, max(1, values["mate"] * 2))
        if "movetime" in values:
            time_limit = values["movetime"]
        elif "infinite" in values or "depth" in values:
            time_limit = None
        else:
            remaining_key = "wtime" if self.position.side_to_move == WHITE else "btime"
            increment_key = "winc" if self.position.side_to_move == WHITE else "binc"
            remaining = values.get(remaining_key)
            if remaining is None:
                time_limit = None
            else:
                moves_to_go = max(values.get("movestogo", 30), 1)
                increment = values.get(increment_key, 0)
                budget = remaining // moves_to_go + increment * 3 // 4
                safe_remaining = max(remaining - self.move_overhead_ms, 1)
                time_limit = max(1, min(budget, safe_remaining))
        return {
            "depth": max(depth, 1),
            "time_limit_ms": time_limit,
            "node_limit": values.get("nodes"),
        }

    def stop_search(self):
        if self.search_thread is None:
            return
        if self.search_thread.is_alive():
            self.stop_event.set()
            self.search_thread.join(timeout=10)
        self.search_thread = None
        self.stop_event = None

    def wait_for_search(self, timeout=None):
        thread = self.search_thread
        if thread is not None:
            thread.join(timeout=timeout)
        return thread is None or not thread.is_alive()

    def run(self, input_stream=None):
        input_stream = input_stream or sys.stdin
        for line in input_stream:
            try:
                if not self.handle_line(line):
                    break
            except (ValueError, IndexError) as error:
                self.send(f"info string {error}")
