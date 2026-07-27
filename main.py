"""Small command-line entry point for move-generation verification."""

import argparse

from engine.constants import START_FEN
from engine.fen import load_fen
from engine.perft import divide, perft
from engine.position import Position
from engine.move import move_to_string
from engine.search import Searcher
from engine.uci import UCIEngine


def main():
    parser = argparse.ArgumentParser(description="Adaptive Chess Engine tools")
    parser.add_argument("--fen", default=START_FEN, help="position in FEN notation")
    parser.add_argument("--perft", type=int, help="count legal leaf nodes at this depth")
    parser.add_argument("--divide", type=int, help="show per-root-move perft counts")
    parser.add_argument("--search-depth", type=int, help="search for the best move")
    parser.add_argument("--uci", action="store_true", help="run the UCI engine")
    args = parser.parse_args()

    if args.uci or (
        args.perft is None
        and args.divide is None
        and args.search_depth is None
    ):
        UCIEngine().run()
        return

    position = Position()
    load_fen(position, args.fen)
    if args.divide is not None:
        counts = divide(position, args.divide)
        for move, nodes in sorted(counts.items()):
            print(f"{move}: {nodes}")
        print(f"Nodes: {sum(counts.values())}")
    elif args.perft is not None:
        print(perft(position, args.perft))
    elif args.search_depth is not None:
        result = Searcher().search(position, args.search_depth)
        bestmove = move_to_string(result.best_move) if result.best_move is not None else "0000"
        pv = " ".join(move_to_string(move) for move in result.pv)
        print(f"bestmove {bestmove}")
        print(f"score cp {result.score}")
        print(f"depth {result.depth}")
        print(f"nodes {result.nodes}")
        print(f"pv {pv}")
    else:
        position.print()


if __name__ == "__main__":
    main()
