"""Reproducible fixed-node reference analysis for PGN decision records."""

from __future__ import annotations

import hashlib
import json
import queue
import re
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .fen import load_fen
from .move import move_to_string
from .movegen import generate_legal_moves
from .opponent_labels import label_decision
from .pgn_dataset import DecisionRecord
from .position import Position


ANALYSIS_VERSION = 1


@dataclass(frozen=True, slots=True)
class ReferenceResult:
    score_cp: int | None
    mate_in: int | None
    best_move_uci: str
    depth: int
    nodes: int


@dataclass(frozen=True, slots=True)
class AnalyzedDecision:
    decision: DecisionRecord
    analysis_version: int
    reference_engine: str
    reference_nodes: int
    reference_best_move_uci: str
    best_score_cp: int | None
    played_score_cp: int | None
    best_mate_in: int | None
    played_mate_in: int | None
    centipawn_loss: int | None
    large_error: bool | None
    label_eligible: bool
    exclusion_reason: str | None

    def to_dict(self) -> dict:
        result = asdict(self.decision)
        result.update({key: value for key, value in asdict(self).items() if key != "decision"})
        return result


def _last_int(tokens: list[str], name: str, default: int = 0) -> int:
    try:
        return int(tokens[tokens.index(name) + 1])
    except (ValueError, IndexError):
        return default


def parse_reference_output(lines: Iterable[str]) -> ReferenceResult:
    score_cp = mate_in = None
    depth = nodes = 0
    best_move = ""
    for line in lines:
        tokens = line.split()
        if tokens[:1] == ["info"] and "score" in tokens:
            score_index = tokens.index("score")
            if score_index + 2 < len(tokens):
                kind, raw = tokens[score_index + 1], tokens[score_index + 2]
                if re.fullmatch(r"-?\d+", raw):
                    if kind == "cp":
                        score_cp, mate_in = int(raw), None
                    elif kind == "mate":
                        mate_in, score_cp = int(raw), None
            depth = _last_int(tokens, "depth", depth)
            nodes = _last_int(tokens, "nodes", nodes)
        elif tokens[:1] == ["bestmove"] and len(tokens) >= 2:
            best_move = tokens[1]
    if score_cp is None and mate_in is None:
        raise ValueError("reference engine returned no score")
    return ReferenceResult(score_cp, mate_in, best_move, depth, nodes)


class FixedNodeReferenceEngine:
    def __init__(self, path: str | Path, nodes: int = 50_000, hash_mb: int = 64):
        if nodes < 1:
            raise ValueError("reference nodes must be positive")
        self.nodes = nodes
        self.process = subprocess.Popen(
            [str(Path(path).resolve())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        self.lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self._send("uci")
        handshake = self._collect_until("uciok", 10)
        self.name = next((line[8:] for line in handshake if line.startswith("id name ")), Path(path).name)
        for name, value in (("Threads", 1), ("Hash", hash_mb), ("MultiPV", 1)):
            self._send(f"setoption name {name} value {value}")
        self._ready()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.lines.put(line.strip())

    def _send(self, command: str) -> None:
        if self.process.poll() is not None or self.process.stdin is None:
            raise RuntimeError("reference engine is not running")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def _collect_until(self, prefix: str, timeout: float) -> list[str]:
        deadline = time.monotonic() + timeout
        collected = []
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            collected.append(line)
            if line.startswith(prefix):
                return collected
        raise TimeoutError(f"reference engine did not return {prefix}")

    def _ready(self) -> None:
        self._send("isready")
        self._collect_until("readyok", 10)

    def analyze(self, fen: str, moves: tuple[str, ...] = ()) -> ReferenceResult:
        self._send("setoption name Clear Hash")
        self._ready()
        suffix = " moves " + " ".join(moves) if moves else ""
        self._send(f"position fen {fen}{suffix}")
        self._send(f"go nodes {self.nodes}")
        # Node-limited work is deterministic, but wall time varies sharply by
        # position and host contention. The timeout is only a hang detector.
        return parse_reference_output(self._collect_until("bestmove ", max(60, self.nodes / 1_000)))

    def close(self) -> None:
        if self.process.poll() is None:
            self._send("quit")
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _validate_played_move(record: DecisionRecord) -> None:
    position = Position()
    load_fen(position, record.fen_before)
    legal = {move_to_string(move) for move in generate_legal_moves(position)}
    if record.played_uci not in legal:
        raise ValueError(f"dataset move {record.played_uci} is illegal in {record.fen_before}")


def analyze_decision(record: DecisionRecord, engine: FixedNodeReferenceEngine) -> AnalyzedDecision:
    _validate_played_move(record)
    best = engine.analyze(record.fen_before)
    played_child = engine.analyze(record.fen_before, (record.played_uci,))
    played_score = -played_child.score_cp if played_child.score_cp is not None else None
    played_mate = -played_child.mate_in if played_child.mate_in is not None else None
    if best.score_cp is None or played_score is None:
        label = label_decision(0, 0, best_is_mate=best.mate_in is not None, played_is_mate=played_mate is not None)
    else:
        label = label_decision(best.score_cp, played_score)
    return AnalyzedDecision(
        record, ANALYSIS_VERSION, engine.name, engine.nodes, best.best_move_uci,
        best.score_cp, played_score, best.mate_in, played_mate,
        label.centipawn_loss, label.large_error, label.eligible, label.exclusion_reason,
    )


def load_decisions_jsonl(path: str | Path) -> tuple[DecisionRecord, ...]:
    records = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(DecisionRecord(**json.loads(line)))
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid decision JSONL at line {line_number}: {error}") from error
    return tuple(records)


def deterministic_decision_sample(
    records: tuple[DecisionRecord, ...], size: int,
) -> tuple[DecisionRecord, ...]:
    """Select a stable pseudo-random subset, returning rows in source order."""
    if size < 0:
        raise ValueError("sample size cannot be negative")
    if size >= len(records):
        return records
    ranked = sorted(
        enumerate(records),
        key=lambda item: hashlib.sha256(
            f"{item[1].game_id}:{item[1].ply}".encode("utf-8")
        ).digest(),
    )[:size]
    return tuple(record for _, record in sorted(ranked))


def write_analyzed_jsonl(records: Iterable[AnalyzedDecision], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json.dumps(record.to_dict(), sort_keys=True) + "\n" for record in records), encoding="utf-8")


def load_analyzed_jsonl(path: str | Path) -> tuple[dict, ...]:
    records = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid analyzed JSONL at line {line_number}: {error}") from error
        if not isinstance(record, dict):
            raise ValueError(f"invalid analyzed JSONL at line {line_number}: expected object")
        records.append(record)
    return tuple(records)


def validate_resume_prefix(
    decisions: tuple[DecisionRecord, ...], analyzed: tuple[dict, ...], reference_nodes: int,
) -> None:
    """Reject partial outputs that are not an exact prefix of this analysis run."""
    if len(analyzed) > len(decisions):
        raise ValueError("resume output contains more rows than the input dataset")
    identity_fields = ("game_id", "ply", "fen_before", "played_uci")
    for index, (decision, existing) in enumerate(zip(decisions, analyzed), 1):
        expected = asdict(decision)
        if any(existing.get(field) != expected[field] for field in identity_fields):
            raise ValueError(f"resume output does not match input at row {index}")
        if existing.get("analysis_version") != ANALYSIS_VERSION:
            raise ValueError(f"resume output has incompatible analysis version at row {index}")
        if existing.get("reference_nodes") != reference_nodes:
            raise ValueError(f"resume output has incompatible node budget at row {index}")
