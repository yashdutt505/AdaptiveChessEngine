#include "ace/attacks.hpp"
#include <cassert>
#include <cstdint>

int main(){
    constexpr int diagonals[4][2]={{-1,-1},{-1,1},{1,-1},{1,1}};
    constexpr int orthogonals[4][2]={{-1,0},{1,0},{0,-1},{0,1}};
    std::uint64_t state=0x243f6a8885a308d3ULL;
    for(int sample=0;sample<2000;++sample){state^=state<<13;state^=state>>7;state^=state<<17;const ace::Bitboard occupied=state;for(int square=0;square<64;++square){assert(ace::bishop_attacks(square,occupied)==ace::ray_attacks(square,occupied,diagonals,4));assert(ace::rook_attacks(square,occupied)==ace::ray_attacks(square,occupied,orthogonals,4));}}
}
