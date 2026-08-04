#include "ace/movegen.hpp"

#include <cassert>

void check(const char* fen, int depth, std::uint64_t expected) {
    ace::Position position;
    ace::load_fen(position, fen);
    const std::string original = ace::to_fen(position);
    const std::uint64_t hash = position.hash_key;
    assert(ace::perft(position, depth) == expected);
    assert(ace::to_fen(position) == original);
    assert(position.hash_key == hash);
    assert(position.history.empty());
}

int main() {
    check("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4, 197281);
    check("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862);
    check("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238);
}
