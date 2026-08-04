#include "ace/search.hpp"
#include <cassert>

int main(){
    ace::Position p; ace::TranspositionTable tt(16); ace::Searcher s(&tt);
    ace::load_fen(p,"7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"); auto mate=s.search(p,2); assert(mate.score>=ace::MateScore-2);
    ace::load_fen(p,"q6k/8/8/8/8/8/8/R5K1 w - - 0 1"); auto queen=s.search(p,2); assert(ace::from_square(queen.best_move)==0&&ace::to_square(queen.best_move)==56);
    ace::load_fen(p,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"); auto start=s.search(p,4); assert(start.best_move!=0&&start.nodes>0);
}
