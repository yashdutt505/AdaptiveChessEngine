"""Small command-line entry point for move-generation verification."""

import argparse
from pathlib import Path

from engine.constants import START_FEN
from engine.fen import load_fen
from engine.perft import divide, perft
from engine.position import Position
from engine.move import move_to_string
from engine.search import Searcher
from engine.uci import UCIEngine
from engine.transposition import TranspositionTable
from engine.benchmark import run_performance_benchmark, run_tactical_benchmark
from engine.selfplay import play_fixed_node_game
from engine.epd import parse_epd_line, run_epd_cases


def main():
    parser = argparse.ArgumentParser(description="Adaptive Chess Engine tools")
    parser.add_argument("--fen", default=START_FEN, help="position in FEN notation")
    parser.add_argument("--perft", type=int, help="count legal leaf nodes at this depth")
    parser.add_argument("--divide", type=int, help="show per-root-move perft counts")
    parser.add_argument("--search-depth", type=int, help="search for the best move")
    parser.add_argument("--uci", action="store_true", help="run the UCI engine")
    parser.add_argument("--benchmark-depth", type=int, help="run tactical benchmark")
    parser.add_argument("--performance", action="store_true", help="run repeatable speed baseline")
    parser.add_argument("--selfplay-nodes", type=int, help="play one fixed-node self-play game")
    parser.add_argument("--selfplay-plies", type=int, default=200, help="maximum self-play plies")
    parser.add_argument("--epd", help="run best-move tests from an EPD file")
    parser.add_argument("--epd-nodes", type=int, default=10000, help="nodes per EPD case")
    args = parser.parse_args()

    if args.uci or (
        args.perft is None
        and args.divide is None
        and args.search_depth is None
        and args.benchmark_depth is None
        and not args.performance
        and args.selfplay_nodes is None
        and args.epd is None
    ):
        UCIEngine().run()
        return

    position = Position()
    load_fen(position, args.fen)
    if args.epd is not None:
        cases = [
            case for line in Path(args.epd).read_text(encoding="utf-8").splitlines()
            if (case := parse_epd_line(line)) is not None
        ]
        results = run_epd_cases(cases, args.epd_nodes)
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(
                f'{status} {result["name"]}: {result["move"]} '
                f'(depth {result["depth"]}, {result["nodes"]} nodes)'
            )
        print(f'Passed: {sum(result["passed"] for result in results)}/{len(results)}')
    elif args.selfplay_nodes is not None:
        result = play_fixed_node_game(args.selfplay_nodes, args.selfplay_plies, args.fen)
        print("moves " + " ".join(result.moves))
        print(f"result {result.result} ({result.reason})")
        print(f"nodes {result.nodes}")
    elif args.performance:
        result = run_performance_benchmark()
        print(
            f'perft depth {result["perft_depth"]}: {result["perft_nodes"]} nodes '
            f'in {result["perft_ms"]} ms ({result["perft_nps"]} nps)'
        )
        print(
            f'search depth {result["search_depth"]}: {result["search_nodes"]} nodes '
            f'in {result["search_ms"]} ms ({result["search_nps"]} nps), '
            f'bestmove {result["best_move"]}'
        )
    elif args.benchmark_depth is not None:
        results = run_tactical_benchmark(args.benchmark_depth)
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(
                f'{status} {result["name"]}: {result["move"]} '
                f'({result["nodes"]} nodes, {result["time_ms"]} ms)'
            )
        passed = sum(result["passed"] for result in results)
        print(f"Passed: {passed}/{len(results)}")
    elif args.divide is not None:
        counts = divide(position, args.divide)
        for move, nodes in sorted(counts.items()):
            print(f"{move}: {nodes}")
        print(f"Nodes: {sum(counts.values())}")
    elif args.perft is not None:
        print(perft(position, args.perft))
    elif args.search_depth is not None:
        result = Searcher(
            transposition_table=TranspositionTable(64)
        ).search(position, args.search_depth)
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
