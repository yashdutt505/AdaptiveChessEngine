#include "ace/core.hpp"

#include <cassert>

int main() {
    using namespace ace;
    constexpr Move move = encode_move(12, 28, WhitePawn, Empty, Empty, 2);
    static_assert(from_square(move) == 12);
    static_assert(to_square(move) == 28);
    static_assert(moving_piece(move) == WhitePawn);
    static_assert(move_flags(move) == 2);

    Board board;
    board.add(4, WhiteKing);
    board.add(60, BlackKing);
    board.add(12, WhitePawn);
    assert(board.valid());
    board.move(12, 28);
    assert(board.squares[28] == WhitePawn);
    assert(board.valid());
    board.remove(28);
    assert(board.valid());
}
