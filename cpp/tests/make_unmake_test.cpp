#include "ace/position.hpp"

#include <cassert>
#include <string>

void round_trip(const char* fen, ace::Move move) {
    ace::Position position;
    ace::load_fen(position, fen);
    const std::string original = ace::to_fen(position);
    const std::uint64_t hash = position.hash_key;
    position.make_move(move);
    assert(position.board.valid());
    assert(position.hash_key == ace::compute_hash(position));
    position.unmake_move();
    assert(position.board.valid());
    assert(position.hash_key == hash);
    assert(position.hash_key == ace::compute_hash(position));
    assert(ace::to_fen(position) == original);
}

int main() {
    using namespace ace;
    round_trip(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        encode_move(12, 28, WhitePawn, Empty, Empty, DoublePawnPush)
    );
    round_trip("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1",
        encode_move(28, 35, WhitePawn, BlackPawn, Empty, Capture));
    round_trip("8/P7/8/8/8/8/8/k6K w - - 0 1",
        encode_move(48, 56, WhitePawn, Empty, WhiteQueen, Promotion));
    round_trip("4k2r/8/8/8/8/8/8/4K2R w Kk - 0 1",
        encode_move(4, 6, WhiteKing, Empty, Empty, KingCastle));
    round_trip("r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 1",
        encode_move(4, 2, WhiteKing, Empty, Empty, QueenCastle));
    round_trip("8/8/8/3pP3/8/8/8/k6K w - d6 0 1",
        encode_move(36, 43, WhitePawn, BlackPawn, Empty, Capture | EnPassant));
}
