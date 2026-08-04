#include "ace/position.hpp"

#include <cassert>
#include <stdexcept>

int main() {
    using namespace ace;
    constexpr const char* start =
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    Position position;
    load_fen(position, start);
    assert(position.board.valid());
    assert(position.white_king == 4 && position.black_king == 60);
    assert(to_fen(position) == start);

    constexpr const char* complex =
        "r3k2r/ppp2ppp/2n5/3pp3/3PP3/2N5/PPP2PPP/R3K2R b KQkq e3 4 12";
    load_fen(position, complex);
    assert(to_fen(position) == complex);

    bool rejected = false;
    try { load_fen(position, "8/8/8/8/8/8/8/8 w - -"); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);
}
