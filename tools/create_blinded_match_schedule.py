"""Create a balanced hidden-arm human-match schedule and public hash commitment."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from engine.constants import START_FEN
from engine.fen import load_fen
from engine.move import move_to_string
from engine.movegen import generate_legal_moves
from engine.position import Position


ARMS = ("neutral", "population", "personal", "random")
COLORS = ("white", "black")
OPENINGS = (
    ("e2e4", "e7e5", "g1f3", "b8c6"), ("d2d4", "d7d5", "c2c4", "e7e6"),
    ("e2e4", "c7c5", "g1f3", "d7d6"), ("g1f3", "d7d5", "d2d4", "g8f6"),
    ("c2c4", "e7e5", "b1c3", "g8f6"), ("e2e4", "e7e6", "d2d4", "d7d5"),
    ("d2d4", "g8f6", "c2c4", "g7g6"), ("e2e4", "c7c6", "d2d4", "d7d5"),
    ("c2c4", "c7c5", "b1c3", "b8c6"), ("g1f3", "g8f6", "g2g3", "g7g6"),
    ("d2d4", "f7f5", "c2c4", "g8f6"), ("e2e4", "d7d5", "e4d5", "d8d5"),
    ("e2e4", "g7g6", "d2d4", "f8g7"), ("d2d4", "e7e6", "c2c4", "f7f5"),
    ("c2c4", "g8f6", "b1c3", "e7e5"), ("g2g3", "d7d5", "f1g2", "e7e5"),
    ("b2b3", "e7e5", "c1b2", "b8c6"), ("e2e4", "b8c6", "d2d4", "e7e5"),
    ("d2d4", "d7d6", "c2c4", "e7e5"), ("g1f3", "c7c5", "e2e4", "b8c6"),
)


def validate_openings() -> None:
    for opening in OPENINGS:
        position=Position();load_fen(position,START_FEN)
        for text in opening:
            matches=[move for move in generate_legal_moves(position) if move_to_string(move)==text]
            if len(matches)!=1:raise ValueError(f"illegal opening move {text} in {opening}")
            position.make_move(matches[0])


def make_block(rng: random.Random, phase: str, block: int, opening: tuple[str,...], first_game: int) -> list[dict]:
    assignments=[(arm,color) for arm in ARMS for color in COLORS];rng.shuffle(assignments)
    return [{
        "phase":phase,"game":first_game+offset,"block":block,"code":secrets.token_hex(5).upper(),
        "arm":arm,"player_color":color,"opening_moves":list(opening),
    } for offset,(arm,color) in enumerate(assignments)]


def create_schedule(seed: int) -> dict:
    validate_openings();rng=random.Random(seed);opening_order=list(OPENINGS);rng.shuffle(opening_order)
    sessions=make_block(rng,"pilot",1,opening_order[0],1);game=1
    for block in range(1,21):
        sessions.extend(make_block(rng,"confirmatory",block,opening_order[block-1],game))
        game+=8
    return {
        "schema_version":1,"created_for":"YashDutt7 blinded adaptive selector experiment",
        "seed":seed,"engine_nodes":5000,"multipv":8,"target_rating":1164,"engine_rating":1223,
        "pilot_games":8,"confirmatory_games":160,"sessions":sessions,
    }


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--private-output",type=Path,required=True)
    parser.add_argument("--public-output",type=Path,required=True);args=parser.parse_args()
    schedule=create_schedule(secrets.randbits(64));private=json.dumps(schedule,indent=2)+"\n"
    args.private_output.parent.mkdir(parents=True,exist_ok=True);args.public_output.parent.mkdir(parents=True,exist_ok=True)
    args.private_output.write_text(private,encoding="utf-8")
    digest=hashlib.sha256(args.private_output.read_bytes()).hexdigest()
    public={
        "schema_version":1,"private_schedule_sha256":digest,"engine_nodes":schedule["engine_nodes"],
        "multipv":schedule["multipv"],"pilot_games":schedule["pilot_games"],
        "confirmatory_games":schedule["confirmatory_games"],
        "sessions":[{key:item[key] for key in ("phase","game","block","code","player_color","opening_moves")} for item in schedule["sessions"]],
    }
    args.public_output.write_text(json.dumps(public,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"private_schedule_sha256":digest,"public_output":str(args.public_output),"sessions":len(schedule["sessions"])},indent=2))


if __name__=="__main__":main()
