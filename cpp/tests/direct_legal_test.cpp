#include "ace/movegen.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>

int main(){
    ace::Position position;
    ace::load_fen(position,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    std::uint32_t state=0x9e3779b9U;
    for(int sample=0;sample<500;++sample){
        auto direct=ace::legal_moves(position);auto reference=ace::legal_moves_reference(position);
        std::sort(direct.begin(),direct.end());std::sort(reference.begin(),reference.end());assert(direct==reference);
        if(direct.empty()||position.halfmove_clock>=100){ace::load_fen(position,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");continue;}
        state=state*1664525U+1013904223U;position.make_move(direct[state%direct.size()]);
    }
}
