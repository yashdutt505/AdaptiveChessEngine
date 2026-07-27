from engine.fen import load_fen
from engine.move import move_to_string
from engine.movegen import generate_legal_moves
from engine.position import Position


def position_from_fen(fen):
    position = Position()
    load_fen(position, fen)
    return position


def legal_move(position, uci):
    matches = [move for move in generate_legal_moves(position) if move_to_string(move) == uci]
    if len(matches) != 1:
        raise AssertionError(f"Expected one legal move {uci}, found {len(matches)}")
    return matches[0]
