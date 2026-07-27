"""Small command-line entry point for move-generation verification."""

import argparse

from engine.constants import START_FEN
from engine.fen import load_fen
from engine.perft import divide, perft
from engine.position import Position


def main():
    parser = argparse.ArgumentParser(description="Adaptive Chess Engine tools")
    parser.add_argument("--fen", default=START_FEN, help="position in FEN notation")
    parser.add_argument("--perft", type=int, help="count legal leaf nodes at this depth")
    parser.add_argument("--divide", type=int, help="show per-root-move perft counts")
    args = parser.parse_args()

    position = Position()
    load_fen(position, args.fen)

    if args.divide is not None:
        counts = divide(position, args.divide)
        for move, nodes in sorted(counts.items()):
            print(f"{move}: {nodes}")
        print(f"Nodes: {sum(counts.values())}")
    elif args.perft is not None:
        print(perft(position, args.perft))
    else:
        position.print()


if __name__ == "__main__":
    main()
