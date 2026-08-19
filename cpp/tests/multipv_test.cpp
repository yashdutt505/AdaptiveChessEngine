#include "ace/search.hpp"

#include <algorithm>
#include <atomic>
#include <cassert>
#include <set>
#include <stdexcept>

namespace {
constexpr const char* StartFen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

bool contains(const ace::MoveList& moves,ace::Move move){
    return std::find(moves.begin(),moves.end(),move)!=moves.end();
}
}

int main(){
    ace::Position position;ace::load_fen(position,StartFen);const auto original_fen=ace::to_fen(position);const auto original_hash=position.hash_key;
    ace::TranspositionTable table(16);ace::Searcher searcher(&table);const auto legal=ace::legal_moves(position);
    ace::SearchLimits deterministic_limits;deterministic_limits.nodes=1000000;
    const auto result=searcher.search_root_candidates(position,2,4,deterministic_limits);
    assert(result.completed&&result.completed_depth==2&&result.requested_count==4);
    assert(result.legal_root_moves==legal.size()&&result.searched_root_moves==legal.size()&&result.all_root_moves_searched);
    assert(result.candidates.size()==4&&result.nodes>0&&result.time_ms>=0);
    std::set<ace::Move> unique;
    for(std::size_t index=0;index<result.candidates.size();++index){
        const auto& candidate=result.candidates[index];
        assert(candidate.completed&&candidate.depth==2&&candidate.nodes>0&&candidate.time_ms>=0);
        assert(contains(legal,candidate.best_move)&&!candidate.pv.empty()&&candidate.pv.front()==candidate.best_move);
        assert(unique.insert(candidate.best_move).second);
        if(index)assert(result.candidates[index-1].score>=candidate.score);
    }
    assert(ace::to_fen(position)==original_fen&&position.hash_key==original_hash);

    ace::Position repeated_position;ace::load_fen(repeated_position,StartFen);ace::TranspositionTable repeated_table(16);ace::Searcher repeated_searcher(&repeated_table);
    const auto repeated=repeated_searcher.search_root_candidates(repeated_position,2,4,deterministic_limits);
    assert(repeated.completed&&repeated.candidates.size()==result.candidates.size());
    for(std::size_t index=0;index<result.candidates.size();++index){
        assert(repeated.candidates[index].best_move==result.candidates[index].best_move);
        assert(repeated.candidates[index].score==result.candidates[index].score);
        assert(repeated.candidates[index].pv==result.candidates[index].pv);
    }

    std::atomic<bool> stop{true};ace::SearchLimits stopped_limits;stopped_limits.stop=&stop;
    const auto interrupted=searcher.search_root_candidates(position,4,4,stopped_limits);
    assert(!interrupted.completed&&interrupted.completed_depth==0&&!interrupted.all_root_moves_searched);
    assert(interrupted.searched_root_moves==0&&interrupted.legal_root_moves==legal.size()&&interrupted.candidates.empty());
    assert(ace::to_fen(position)==original_fen&&position.hash_key==original_hash);

    ace::Position checkmate;ace::load_fen(checkmate,"7k/6Q1/6K1/8/8/8/8/8 b - - 0 1");
    const auto mate_result=searcher.search_root_candidates(checkmate,3,4);
    assert(mate_result.completed&&mate_result.completed_depth==3&&mate_result.all_root_moves_searched);
    assert(mate_result.legal_root_moves==0&&mate_result.searched_root_moves==0&&mate_result.candidates.empty());

    ace::Position stalemate;ace::load_fen(stalemate,"7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
    const auto stale_result=searcher.search_root_candidates(stalemate,3,4);
    assert(stale_result.completed&&stale_result.completed_depth==3&&stale_result.all_root_moves_searched);
    assert(stale_result.legal_root_moves==0&&stale_result.searched_root_moves==0&&stale_result.candidates.empty());

    bool bad_depth=false,bad_count=false;
    try{searcher.search_root_candidates(position,0,4);}catch(const std::invalid_argument&){bad_depth=true;}
    try{searcher.search_root_candidates(position,2,0);}catch(const std::invalid_argument&){bad_count=true;}
    assert(bad_depth&&bad_count);
}
