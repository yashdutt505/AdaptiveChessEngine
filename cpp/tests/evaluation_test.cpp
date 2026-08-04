#include "ace/evaluation.hpp"
#include <cassert>

void check(const char* fen, int expected) {
    ace::Position position; ace::load_fen(position, fen); assert(ace::evaluate(position) == expected);
}

int main() {
    check("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 0);
    check("7k/8/8/8/8/8/8/Q5K1 w - - 0 1", 904);
    check("7k/4P3/8/8/8/8/8/7K w - - 0 1", 271);
    check("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 1);
}
