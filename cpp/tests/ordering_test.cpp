#include "ace/ordering.hpp"
#include <cassert>

ace::Move named(ace::Position& position,const char* text){for(auto move:ace::legal_moves(position))if(ace::square_to_string(ace::from_square(move))+ace::square_to_string(ace::to_square(move))==text)return move;return 0;}
int main(){
    ace::Position position;
    ace::load_fen(position,"6k1/8/4p3/3p4/2P5/8/8/6K1 w - - 0 1");auto even=named(position,"c4d5");assert(even&&ace::static_exchange_eval(position,even)==0);
    ace::load_fen(position,"6k1/8/8/4p3/3p4/8/8/3Q2K1 w - - 0 1");auto poisoned=named(position,"d1d4");assert(poisoned&&ace::static_exchange_eval(position,poisoned)<0);
    ace::load_fen(position,"q6k/8/8/8/8/8/8/R5K1 w - - 0 1");auto winning=named(position,"a1a8");assert(winning&&ace::static_exchange_eval(position,winning)>0);
    ace::load_fen(position,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");auto cutoff=named(position,"g1f3"),failed_move=named(position,"b1c3"),previous=named(position,"e2e4");
    ace::SearchHeuristics heuristics;ace::MoveList failed;failed.push_back(failed_move);heuristics.record_cutoff(cutoff,4,2,0,1,previous,failed);assert(heuristics.killer_rank(cutoff,2)==2);assert(heuristics.history_score(cutoff,0)==16);assert(heuristics.is_countermove(cutoff,previous));assert(heuristics.history_score(failed_move,0)<0);
}
