#include "ace/search.hpp"
#include <atomic>
#include <cassert>

int main(){
    ace::Position p; ace::TranspositionTable tt(16); ace::Searcher s(&tt);
    ace::load_fen(p,"7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"); auto mate=s.search(p,2); assert(mate.score>=ace::MateScore-2);
    ace::load_fen(p,"q6k/8/8/8/8/8/8/R5K1 w - - 0 1"); auto queen=s.search(p,2); assert(ace::from_square(queen.best_move)==0&&ace::to_square(queen.best_move)==56);
    ace::load_fen(p,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"); auto start=s.search(p,4); assert(start.best_move!=0&&start.nodes>0);
    auto reused=s.search(p,2); assert(reused.best_move!=0&&reused.completed);
    const auto fen=ace::to_fen(p); ace::SearchLimits node_limit; node_limit.nodes=100; auto bounded=s.search(p,8,node_limit); assert(!bounded.completed&&bounded.nodes<=100&&ace::to_fen(p)==fen);
    std::atomic<bool> stop{true}; ace::SearchLimits stopped_limit; stopped_limit.stop=&stop; auto stopped=s.search(p,8,stopped_limit); assert(!stopped.completed&&stopped.nodes==0&&ace::to_fen(p)==fen);
    ace::SearchLimits timed; timed.deadline=std::chrono::steady_clock::now(); auto timeout=s.search(p,8,timed); assert(!timeout.completed&&ace::to_fen(p)==fen);
}
