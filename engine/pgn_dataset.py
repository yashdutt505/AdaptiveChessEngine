"""Dependency-free PGN parsing and chronological opponent-decision extraction."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .constants import BLACK, START_FEN, WHITE
from .fen import load_fen, position_to_fen
from .move import (
    from_square,
    is_capture,
    is_kingside_castle,
    is_promotion,
    is_queenside_castle,
    move_to_string,
    moving_piece,
    promotion_piece,
    to_square,
)
from .movegen import generate_legal_moves
from .pieces import Piece
from .position import Position
from .squares import FILES, RANKS, file_of, rank_of, square_from_string


DATASET_VERSION = 1
RESULT_TOKENS = frozenset({"1-0", "0-1", "1/2-1/2", "*"})
PIECE_KIND = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6}
PROMOTION_KIND = {"N": 2, "B": 3, "R": 4, "Q": 5}


@dataclass(frozen=True, slots=True)
class ParsedGame:
    game_id: str
    tags: dict[str, str]
    san_moves: tuple[str, ...]
    source_index: int


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    dataset_version: int
    game_id: str
    game_date: str
    source_index: int
    split: str
    player: str
    player_color: str
    opponent: str
    ply: int
    move_number: int
    fen_before: str
    played_san: str
    played_uci: str
    result: str
    time_control: str
    player_rating: int | None
    opponent_rating: int | None


def _strip_movetext_noise(text: str) -> str:
    output = []
    brace_depth = variation_depth = 0
    semicolon = False
    for char in text:
        if semicolon:
            if char in "\r\n":
                semicolon = False
                output.append(" ")
            continue
        if brace_depth:
            if char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1
            continue
        if variation_depth:
            if char == "(":
                variation_depth += 1
            elif char == ")":
                variation_depth -= 1
            continue
        if char == ";":
            semicolon = True
        elif char == "{":
            brace_depth = 1
        elif char == "(":
            variation_depth = 1
        else:
            output.append(char)
    if brace_depth or variation_depth:
        raise ValueError("unterminated PGN comment or variation")
    return "".join(output)


def _movetext_tokens(text: str) -> tuple[str, ...]:
    cleaned = _strip_movetext_noise(text)
    cleaned = re.sub(r"\$\d+", " ", cleaned)
    cleaned = re.sub(r"(?<!\S)\d+\.(?:\.\.)?", " ", cleaned)
    tokens = []
    for token in cleaned.split():
        token = re.sub(r"^\d+\.(?:\.\.)?", "", token)
        if not token or token in RESULT_TOKENS or token.lower() in {"e.p.", "ep"}:
            continue
        tokens.append(token)
    return tuple(tokens)


def parse_pgn(text: str) -> tuple[ParsedGame, ...]:
    tag_block = re.compile(r'(?m)(?:^\[[A-Za-z0-9_]+\s+"(?:\\.|[^"\\])*"\]\s*\r?\n?)+')
    matches = list(tag_block.finditer(text))
    if not matches:
        raise ValueError("PGN contains no tag blocks")
    games = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        tags = {}
        for key, raw in re.findall(r'^\[([A-Za-z0-9_]+)\s+"((?:\\.|[^"\\])*)"\]\s*$', match.group(), re.MULTILINE):
            tags[key] = raw.replace(r'\"', '"').replace(r"\\", "\\")
        movetext = text[match.end():end]
        moves = _movetext_tokens(movetext)
        identity = tags.get("UUID") or tags.get("Link")
        if not identity:
            digest = hashlib.sha256((json.dumps(tags, sort_keys=True) + "\n" + " ".join(moves)).encode("utf-8")).hexdigest()[:20]
            identity = f"pgn-{digest}"
        games.append(ParsedGame(identity, tags, moves, index))
    return tuple(games)


def parse_san(position: Position, san: str) -> int:
    token = san.strip().replace("0", "O")
    token = re.sub(r"[+#?!]+$", "", token)
    legal = generate_legal_moves(position)
    if token in {"O-O", "O-O-O"}:
        matches = [move for move in legal if is_kingside_castle(move) if token == "O-O"] if token == "O-O" else [move for move in legal if is_queenside_castle(move)]
    else:
        promotion_match = re.search(r"=([NBRQ])$", token)
        promotion_kind = PROMOTION_KIND[promotion_match.group(1)] if promotion_match else None
        core = token[:promotion_match.start()] if promotion_match else token
        destination_match = re.search(r"([a-h][1-8])$", core)
        if not destination_match:
            raise ValueError(f"invalid SAN token: {san}")
        destination = square_from_string(destination_match.group(1))
        prefix = core[:destination_match.start()]
        piece_letter = prefix[0] if prefix and prefix[0] in "NBRQK" else "P"
        if piece_letter != "P":
            prefix = prefix[1:]
        capture = "x" in prefix
        disambiguation = prefix.replace("x", "")
        matches = []
        for move in legal:
            piece_kind = (int(moving_piece(move)) - 1) % 6 + 1
            if piece_kind != PIECE_KIND[piece_letter] or to_square(move) != destination:
                continue
            if is_capture(move) != capture:
                continue
            if promotion_kind is None and is_promotion(move):
                continue
            if promotion_kind is not None:
                if not is_promotion(move) or (int(promotion_piece(move)) - 1) % 6 + 1 != promotion_kind:
                    continue
            source = from_square(move)
            if len(disambiguation) == 1 and disambiguation in FILES and file_of(source) != FILES.index(disambiguation):
                continue
            if len(disambiguation) == 1 and disambiguation in RANKS and rank_of(source) != RANKS.index(disambiguation):
                continue
            if len(disambiguation) == 2 and move_to_string(move)[:2] != disambiguation:
                continue
            matches.append(move)
    if len(matches) != 1:
        raise ValueError(f"SAN {san!r} matched {len(matches)} legal moves in {position_to_fen(position)}")
    return matches[0]


def _date_key(game: ParsedGame) -> tuple[str, int]:
    raw = game.tags.get("UTCDate") or game.tags.get("Date") or "????.??.??"
    normalized = raw.replace("?", "9")
    return normalized, game.source_index


def _rating(tags: dict[str, str], key: str) -> int | None:
    value = tags.get(key, "")
    return int(value) if value.isdigit() else None


def _extract_decisions(
    selected: list[ParsedGame], included_player: str | None = None,
    excluded_player: str | None = None,
) -> tuple[DecisionRecord, ...]:
    selected.sort(key=_date_key)
    count = len(selected)
    train_end = max(1, int(count * 0.6)) if count else 0
    validation_end = max(train_end, int(count * 0.8))
    records = []
    for game_index, game in enumerate(selected):
        split = "train" if game_index < train_end else "validation" if game_index < validation_end else "test"
        tags = game.tags
        white = tags.get("White", "")
        black = tags.get("Black", "")
        position = Position()
        load_fen(position, tags.get("FEN", START_FEN))
        for ply, san in enumerate(game.san_moves):
            move = parse_san(position, san)
            player_is_white = position.side_to_move == WHITE
            player = white if player_is_white else black
            target_match = included_player is None or player.casefold() == included_player.casefold()
            excluded_match = excluded_player is not None and player.casefold() == excluded_player.casefold()
            if target_match and not excluded_match:
                records.append(DecisionRecord(
                    DATASET_VERSION, game.game_id, tags.get("UTCDate") or tags.get("Date", ""),
                    game.source_index, split, player, "white" if player_is_white else "black",
                    black if player_is_white else white, ply, position.fullmove_number,
                    position_to_fen(position), san, move_to_string(move), tags.get("Result", "*"),
                    tags.get("TimeControl", ""), _rating(tags, "WhiteElo" if player_is_white else "BlackElo"),
                    _rating(tags, "BlackElo" if player_is_white else "WhiteElo"),
                ))
            position.make_move(move)
    return tuple(records)


def extract_player_decisions(games: tuple[ParsedGame, ...], player: str) -> tuple[DecisionRecord, ...]:
    target = player.casefold()
    selected = [
        game for game in games
        if game.tags.get("White", "").casefold() == target or game.tags.get("Black", "").casefold() == target
    ]
    return _extract_decisions(selected, included_player=player)


def extract_all_decisions(
    games: tuple[ParsedGame, ...], excluded_player: str | None = None,
) -> tuple[DecisionRecord, ...]:
    """Extract both sides while keeping every game wholly in one chronological split."""
    return _extract_decisions(list(games), excluded_player=excluded_player)


def extract_pgn_file(path: str | Path, player: str) -> tuple[DecisionRecord, ...]:
    return extract_player_decisions(parse_pgn(Path(path).read_text(encoding="utf-8-sig")), player)


def write_jsonl(records: tuple[DecisionRecord, ...], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json.dumps(asdict(record), sort_keys=True) + "\n" for record in records), encoding="utf-8")
