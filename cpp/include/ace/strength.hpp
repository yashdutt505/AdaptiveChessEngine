#pragma once

#include "ace/search.hpp"

#include <cmath>
#include <string>
#include <vector>

namespace ace {
constexpr const char* StandardStartFen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

enum class SprtDecision {Continue,AcceptH0,AcceptH1};

class ScoreSprt {
    double lower_,upper_,p0_,p1_,llr_=0.0;
    int games_=0;
    static double expected(double elo){return 1.0/(1.0+std::pow(10.0,-elo/400.0));}
public:
    ScoreSprt(double elo0,double elo1,double alpha=0.05,double beta=0.05):
        lower_(std::log(beta/(1.0-alpha))),upper_(std::log((1.0-beta)/alpha)),p0_(expected(elo0)),p1_(expected(elo1)){}
    SprtDecision record(double score){
        const double bounded=std::max(0.0,std::min(1.0,score));
        llr_+=bounded*std::log(p1_/p0_)+(1.0-bounded)*std::log((1.0-p1_)/(1.0-p0_));++games_;
        return decision();
    }
    SprtDecision decision()const{return llr_>=upper_?SprtDecision::AcceptH1:llr_<=lower_?SprtDecision::AcceptH0:SprtDecision::Continue;}
    double llr()const{return llr_;}int games()const{return games_;}double lower_bound()const{return lower_;}double upper_bound()const{return upper_;}
};

struct SelfPlayConfig {int depth=3;int max_plies=160;std::uint64_t nodes=~std::uint64_t{0};};
struct GameResult {int outcome=0;std::vector<Move> moves;std::string final_fen;};

inline bool repeated(const Position& position){int count=1;for(const auto& undo:position.history)if(undo.hash_key==position.hash_key)++count;return count>=3;}

inline GameResult play_game(const SearchOptions& white_options,const SearchOptions& black_options,const SelfPlayConfig& config={},const std::string& fen=StandardStartFen){
    Position position;load_fen(position,fen);TranspositionTable white_table(16),black_table(16);Searcher white(&white_table,white_options),black(&black_table,black_options);GameResult result;
    for(int ply=0;ply<config.max_plies;++ply){
        auto moves=legal_moves(position);if(moves.empty()){if(in_check(position,position.side_to_move))result.outcome=position.side_to_move==0?-1:1;break;}
        if(position.halfmove_clock>=100||repeated(position))break;
        SearchLimits limits;limits.nodes=config.nodes;auto search=(position.side_to_move==0?white.search(position,config.depth,limits):black.search(position,config.depth,limits));
        Move move=search.best_move;if(!move)move=moves.front();bool legal=false;for(const auto candidate:moves)if(candidate==move){legal=true;break;}if(!legal)throw std::runtime_error("self-play search returned illegal move");
        result.moves.push_back(move);position.make_move(move);
    }
    result.final_fen=to_fen(position);return result;
}
} // namespace ace
