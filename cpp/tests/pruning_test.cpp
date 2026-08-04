#include "ace/search.hpp"
#include <cassert>
#include <iostream>
#include <vector>

int main(){
    const std::vector<const char*> positions={
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1",
        "4k3/8/8/3p4/3P4/8/4K3/8 w - - 0 1",
        "7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"
    };
    std::uint64_t optimized_nodes=0,reference_nodes=0,applied=0;
    for(const auto fen:positions){
        ace::Position optimized_position,reference_position;ace::load_fen(optimized_position,fen);ace::load_fen(reference_position,fen);
        ace::TranspositionTable optimized_table(16),reference_table(16);ace::Searcher optimized(&optimized_table);ace::Searcher reference(&reference_table,{false,false,false});
        const auto fast=optimized.search(optimized_position,4);const auto full=reference.search(reference_position,4);
        if(!(fast.completed&&full.completed&&fast.score==full.score))std::cerr<<fen<<" fast "<<fast.score<<' '<<fast.best_move<<" full "<<full.score<<' '<<full.best_move<<'\n';
        assert(fast.completed&&full.completed&&fast.score==full.score&&fast.best_move&&full.best_move);
        assert(ace::to_fen(optimized_position)==ace::to_fen(reference_position));
        optimized_nodes+=fast.nodes;reference_nodes+=full.nodes;applied+=optimized.lmr_reductions+optimized.null_prunes+optimized.futility_prunes;
    }
    assert(applied>0);assert(optimized_nodes<reference_nodes);
    ace::Position pawn_only;ace::load_fen(pawn_only,"4k3/8/8/3p4/3P4/8/4K3/8 w - - 99 1");ace::Searcher safeguarded;const auto result=safeguarded.search(pawn_only,5);assert(result.completed&&safeguarded.null_prunes==0&&pawn_only.halfmove_clock==99);
}
