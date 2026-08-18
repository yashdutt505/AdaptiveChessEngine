#include "ace/evaluation.hpp"
#include <cassert>

void check(const char* fen, int expected) {
    ace::Position position; ace::load_fen(position, fen); assert(ace::evaluate(position) == expected);assert(ace::evaluate(position)==ace::evaluate_full(position));
}

int main() {
    check("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 0);
    check("7k/8/8/8/8/8/8/Q5K1 w - - 0 1", 904);
    check("7k/4P3/8/8/8/8/8/7K w - - 0 1", 271);
    check("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 1);
    ace::Position position;ace::load_fen(position,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");const auto original=ace::to_fen(position);std::uint32_t state=7;
    for(int ply=0;ply<300;++ply){assert(ace::evaluate(position)==ace::evaluate_full(position));auto moves=ace::legal_moves(position);if(moves.empty())break;state=state*1664525U+1013904223U;position.make_move(moves[state%moves.size()]);}
    while(!position.history.empty()){assert(ace::evaluate(position)==ace::evaluate_full(position));position.unmake_move();}assert(ace::to_fen(position)==original);assert(ace::evaluate(position)==ace::evaluate_full(position));
}
