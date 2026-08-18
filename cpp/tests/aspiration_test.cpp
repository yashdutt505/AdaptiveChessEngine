#include "ace/iterative.hpp"
#include <cassert>

int main(){
    ace::Position full_position,aspiration_position;const char* fen="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";ace::load_fen(full_position,fen);ace::load_fen(aspiration_position,fen);
    ace::TranspositionTable full_table(16),aspiration_table(16);ace::Searcher full_searcher(&full_table),aspiration_searcher(&aspiration_table);
    const auto full=full_searcher.search(full_position,4);int researches=0;const auto narrowed=ace::aspiration_search(aspiration_position,aspiration_searcher,4,full.score+500,{},25,&researches);
    assert(narrowed.completed&&narrowed.score==full.score&&narrowed.best_move==full.best_move&&researches>0);assert(ace::to_fen(full_position)==ace::to_fen(aspiration_position));
    bool rejected=false;try{full_searcher.search(full_position,2,{},10,10);}catch(const std::invalid_argument&){rejected=true;}assert(rejected);
}
