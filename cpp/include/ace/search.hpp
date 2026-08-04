#pragma once

#include "ace/evaluation.hpp"
#include "ace/transposition.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <limits>

namespace ace {
constexpr int Infinity=1000000, MateScore=100000;
struct SearchLimits {
    std::uint64_t nodes=std::numeric_limits<std::uint64_t>::max();
    std::chrono::steady_clock::time_point deadline=std::chrono::steady_clock::time_point::max();
    std::atomic<bool>* stop=nullptr;
};
struct SearchResult { Move best_move=0; int score=0; int depth=0; std::uint64_t nodes=0; std::vector<Move> pv; long long time_ms=0; bool completed=true; };

class Searcher {
    TranspositionTable* tt_;
    std::chrono::steady_clock::time_point start_;
    SearchLimits limits_{};
    bool stopped_=false;
public:
    std::uint64_t nodes=0;
    explicit Searcher(TranspositionTable* tt=nullptr):tt_(tt){}
    SearchResult search(Position& p,int depth,const SearchLimits& limits={}) {
        nodes=0; stopped_=false; limits_=limits; start_=std::chrono::steady_clock::now(); std::vector<Move> pv;
        const int score=negamax(p,depth,-Infinity,Infinity,0,pv);
        return {pv.empty()?0:pv[0],score,depth,nodes,pv,std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start_).count(),!stopped_};
    }
private:
    bool stop_requested() {
        if(stopped_) return true;
        if(nodes>=limits_.nodes) return stopped_=true;
        if(limits_.stop&&limits_.stop->load(std::memory_order_relaxed)) return stopped_=true;
        if((nodes&1023)==0&&std::chrono::steady_clock::now()>=limits_.deadline) return stopped_=true;
        return false;
    }
    bool draw(const Position& p) const {
        if(p.halfmove_clock>=100) return true;
        int count=1;
        for(const auto& undo:p.history) if(undo.hash_key==p.hash_key) ++count;
        return count>=3;
    }
    std::vector<Move> ordered(Position&,std::vector<Move> moves,Move tt_move) {
        std::sort(moves.begin(),moves.end(),[&](Move a,Move b){return order_score(a,tt_move)>order_score(b,tt_move);}); return moves;
    }
    int order_score(Move move,Move tt_move) const {
        if(move==tt_move) return 2000000;
        if(move_flags(move)&Promotion) return 800000+piece_value(promotion_piece(move));
        if(move_flags(move)&Capture) return 700000+piece_value(captured_piece(move))*16-piece_value(moving_piece(move));
        return 0;
    }
    int quiescence(Position& p,int alpha,int beta,int ply) {
        if(stop_requested()) return 0;
        ++nodes;
        if(draw(p)) return 0;
        const bool checked=in_check(p,p.side_to_move);
        auto moves=legal_moves(p);
        if(checked) { if(moves.empty()) return -MateScore+ply; }
        else {
            const int stand=evaluate(p); if(stand>=beta) return beta; if(stand>alpha) alpha=stand;
            moves.erase(std::remove_if(moves.begin(),moves.end(),[](Move m){return !(move_flags(m)&(Capture|Promotion));}),moves.end());
            if(moves.empty()) return alpha;
        }
        for(Move move:ordered(p,std::move(moves),0)) { p.make_move(move); const int score=-quiescence(p,-beta,-alpha,ply+1); p.unmake_move(); if(stopped_)return 0; if(score>=beta)return beta; if(score>alpha)alpha=score; }
        return alpha;
    }
    int negamax(Position& p,int depth,int alpha,int beta,int ply,std::vector<Move>& pv) {
        if(stop_requested()) return 0;
        ++nodes;
        if(draw(p)) return 0;
        if(depth==0)return quiescence(p,alpha,beta,ply);
        const int original=alpha; Move tt_move=0;
        if(tt_) if(auto* e=tt_->probe(p.hash_key)) { tt_move=e->move; if(e->depth>=depth){int s=e->score; if(s>MateScore-128)s-=ply; if(s<-MateScore+128)s+=ply; if(e->bound==Exact){if(tt_move)pv.assign(1,tt_move);return s;} if(e->bound==Lower)alpha=std::max(alpha,s);else beta=std::min(beta,s);if(alpha>=beta)return s;}}
        auto moves=legal_moves(p); if(moves.empty())return in_check(p,p.side_to_move)?-MateScore+ply:0;
        int best=-Infinity; Move best_move=0; std::vector<Move> best_child; int index=0;
        for(Move move:ordered(p,std::move(moves),tt_move)) {
            p.make_move(move); std::vector<Move> child; int score;
            if(index++==0) score=-negamax(p,depth-1,-beta,-alpha,ply+1,child);
            else { score=-negamax(p,depth-1,-alpha-1,-alpha,ply+1,child); if(score>alpha&&score<beta)score=-negamax(p,depth-1,-beta,-alpha,ply+1,child); }
            p.unmake_move(); if(stopped_)return 0; if(score>best){best=score;best_move=move;best_child=child;} if(score>alpha)alpha=score;if(alpha>=beta)break;
        }
        pv.clear(); if(best_move){pv.push_back(best_move);pv.insert(pv.end(),best_child.begin(),best_child.end());}
        if(tt_){Bound bound=best<=original?Upper:(best>=beta?Lower:Exact);int stored=best;if(stored>MateScore-128)stored+=ply;if(stored<-MateScore+128)stored-=ply;tt_->store(p.hash_key,depth,stored,bound,best_move);}
        return best;
    }
};
} // namespace ace
