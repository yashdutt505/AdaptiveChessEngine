#pragma once

#include "ace/adaptive_features.hpp"
#include "ace/ordering.hpp"
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
struct SearchOptions {bool lmr=true;bool null_move=true;bool futility=true;};
struct SearchResult { Move best_move=0; int score=0; int depth=0; std::uint64_t nodes=0; std::vector<Move> pv; long long time_ms=0; bool completed=true; PositionFeatures features{}; };
struct RootCandidatesResult {
    std::vector<SearchResult> candidates;
    std::uint64_t nodes=0;
    long long time_ms=0;
    int completed_depth=0;
    std::size_t requested_count=0;
    std::size_t legal_root_moves=0;
    std::size_t searched_root_moves=0;
    bool all_root_moves_searched=false;
    bool completed=false;
};
struct PVLine {
    std::array<Move,128> moves{};std::size_t size=0;
    void clear(){size=0;}void assign(Move move){moves[0]=move;size=1;}
    void set(Move move,const PVLine& child){moves[0]=move;size=std::min<std::size_t>(127,child.size)+1;std::copy(child.moves.begin(),child.moves.begin()+size-1,moves.begin()+1);}
};

class Searcher {
    TranspositionTable* tt_;
    std::chrono::steady_clock::time_point start_;
    SearchLimits limits_{};
    bool stopped_=false;
    SearchHeuristics heuristics_{};
    SearchOptions options_{};
public:
    std::uint64_t nodes=0;
    std::uint64_t lmr_reductions=0,null_prunes=0,futility_prunes=0;
    explicit Searcher(TranspositionTable* tt=nullptr,SearchOptions options={}):tt_(tt),options_(options){}
    SearchResult search(Position& p,int depth,const SearchLimits& limits={},int alpha=-Infinity,int beta=Infinity) {
        if(alpha>=beta)throw std::invalid_argument("invalid search window");
        nodes=0;lmr_reductions=0;null_prunes=0;futility_prunes=0;stopped_=false; limits_=limits; start_=std::chrono::steady_clock::now(); PVLine pv;
        const int score=negamax(p,depth,alpha,beta,0,pv);
        std::vector<Move> public_pv(pv.moves.begin(),pv.moves.begin()+pv.size);
        return {pv.size==0?0:pv.moves[0],score,depth,nodes,std::move(public_pv),std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start_).count(),!stopped_};
    }
    RootCandidatesResult search_root_candidates(Position& p,int depth,std::size_t count,const SearchLimits& limits={}) {
        if(depth<1)throw std::invalid_argument("root candidate depth must be at least one");
        if(count<1)throw std::invalid_argument("root candidate count must be at least one");
        nodes=0;lmr_reductions=0;null_prunes=0;futility_prunes=0;stopped_=false;limits_=limits;start_=std::chrono::steady_clock::now();
        RootCandidatesResult result;result.requested_count=count;auto moves=ordered(p,legal_moves(p),0,0);result.legal_root_moves=moves.size();result.candidates.reserve(std::min(count,moves.size()));
        for(const Move move:moves){
            if(stop_requested())break;
            const auto candidate_started=std::chrono::steady_clock::now();const auto before=nodes;p.make_move(move);PVLine child;const int score=-negamax(p,depth-1,-Infinity,Infinity,1,child);p.unmake_move();
            if(stopped_)break;
            std::vector<Move> pv;pv.reserve(child.size+1);pv.push_back(move);pv.insert(pv.end(),child.moves.begin(),child.moves.begin()+child.size);
            const auto candidate_ms=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-candidate_started).count();
            result.candidates.push_back({move,score,depth,nodes-before,std::move(pv),candidate_ms,true,extract_position_features(p,move)});++result.searched_root_moves;
        }
        std::stable_sort(result.candidates.begin(),result.candidates.end(),[](const SearchResult& left,const SearchResult& right){return left.score>right.score;});
        if(result.candidates.size()>count)result.candidates.resize(count);
        result.nodes=nodes;result.time_ms=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start_).count();
        result.all_root_moves_searched=result.searched_root_moves==result.legal_root_moves;
        result.completed=!stopped_&&result.all_root_moves_searched;
        result.completed_depth=result.completed?depth:0;
        return result;
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
    bool has_non_pawn_material(const Position& p,int color)const{
        const int offset=color?6:0;return (p.board.pieces[WhiteKnight+offset]|p.board.pieces[WhiteBishop+offset]|p.board.pieces[WhiteRook+offset]|p.board.pieces[WhiteQueen+offset])!=0;
    }
    struct NullState{int en_passant,halfmove_clock,fullmove_number;std::uint64_t hash_key;};
    NullState make_null(Position& p){
        const NullState state{p.en_passant,p.halfmove_clock,p.fullmove_number,p.hash_key};
        if(p.en_passant!=NoEnPassant)p.hash_key^=zobrist::EnPassantKeys[p.en_passant%8];
        p.en_passant=NoEnPassant;p.side_to_move^=1;p.hash_key^=zobrist::SideKey;return state;
    }
    void unmake_null(Position& p,const NullState& state){p.side_to_move^=1;p.en_passant=state.en_passant;p.halfmove_clock=state.halfmove_clock;p.fullmove_number=state.fullmove_number;p.hash_key=state.hash_key;}
    MoveList ordered(Position& p,MoveList moves,Move tt_move,int ply) {
        const Move previous=p.history.empty()?0:p.history.back().move;
        std::array<int,256> scores{};for(std::size_t index=0;index<moves.size();++index)scores[index]=order_score(p,moves[index],tt_move,ply,previous);
        for(std::size_t index=1;index<moves.size();++index){const Move move=moves[index];const int score=scores[index];std::size_t place=index;while(place>0&&scores[place-1]<score){moves[place]=moves[place-1];scores[place]=scores[place-1];--place;}moves[place]=move;scores[place]=score;}return moves;
    }
    int order_score(const Position& p,Move move,Move tt_move,int ply,Move previous) const {
        if(move==tt_move) return 2000000;
        if(move_flags(move)&Promotion) return 800000+piece_value(promotion_piece(move));
        if(move_flags(move)&Capture) return 700000+static_exchange_eval(p,move)*32+piece_value(captured_piece(move))*16-piece_value(moving_piece(move));
        return heuristics_.killer_rank(move,ply)*100000+(heuristics_.is_countermove(move,previous)?50000:0)+heuristics_.history_score(move,p.side_to_move);
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
        for(Move move:ordered(p,std::move(moves),0,ply)) { p.make_move(move); const int score=-quiescence(p,-beta,-alpha,ply+1); p.unmake_move(); if(stopped_)return 0; if(score>=beta)return beta; if(score>alpha)alpha=score; }
        return alpha;
    }
    int negamax(Position& p,int depth,int alpha,int beta,int ply,PVLine& pv) {
        if(stop_requested()) return 0;
        ++nodes;
        if(draw(p)) return 0;
        if(depth==0)return quiescence(p,alpha,beta,ply);
        const int original=alpha;const bool pv_node=beta-alpha>1;Move tt_move=0;
        if(tt_) if(auto* e=tt_->probe(p.hash_key)) { tt_move=e->move; if(e->depth>=depth){int s=e->score; if(s>MateScore-128)s-=ply; if(s<-MateScore+128)s+=ply; if(e->bound==Exact){if(tt_move)pv.assign(tt_move);return s;} if(e->bound==Lower)alpha=std::max(alpha,s);else beta=std::min(beta,s);if(alpha>=beta)return s;}}
        const bool checked=in_check(p,p.side_to_move);
        if(options_.null_move&&!pv_node&&depth>=3&&!checked&&has_non_pawn_material(p,p.side_to_move)&&evaluate(p)>=beta){
            const auto state=make_null(p);PVLine child;const int reduction=2+depth/4;const int score=-negamax(p,std::max(0,depth-1-reduction),-beta,-beta+1,ply+1,child);unmake_null(p,state);if(stopped_)return 0;if(score>=beta){++null_prunes;return beta;}
        }
        auto moves=legal_moves(p); if(moves.empty())return checked?-MateScore+ply:0;
        const int static_score=options_.futility&&!pv_node&&!checked&&depth==1?evaluate(p):-Infinity;
        int best=-Infinity; Move best_move=0; PVLine best_child; int index=0;MoveList tried_quiets;const Move previous=p.history.empty()?0:p.history.back().move;const int color=p.side_to_move;
        for(Move move:ordered(p,std::move(moves),tt_move,ply)) {
            const int move_index=index++;const bool quiet=!(move_flags(move)&(Capture|Promotion));
            if(options_.futility&&static_score!=-Infinity&&quiet&&move_index>0&&static_score+120<=alpha){++futility_prunes;continue;}
            p.make_move(move); PVLine child; int score;const bool gives_check=in_check(p,p.side_to_move);
            if(move_index==0) score=-negamax(p,depth-1,-beta,-alpha,ply+1,child);
            else {
                const bool reduce=options_.lmr&&depth>=3&&move_index>=3&&quiet&&!checked&&!gives_check;
                if(reduce){++lmr_reductions;score=-negamax(p,depth-2,-alpha-1,-alpha,ply+1,child);if(score>alpha)score=-negamax(p,depth-1,-alpha-1,-alpha,ply+1,child);}
                else score=-negamax(p,depth-1,-alpha-1,-alpha,ply+1,child);
                if(score>alpha&&score<beta)score=-negamax(p,depth-1,-beta,-alpha,ply+1,child);
            }
            p.unmake_move(); if(stopped_)return 0; if(score>best){best=score;best_move=move;best_child=child;} if(score>alpha)alpha=score;if(alpha>=beta){heuristics_.record_cutoff(move,depth,ply,color,index-1,previous,tried_quiets);break;}if(!(move_flags(move)&(Capture|Promotion)))tried_quiets.push_back(move);
        }
        if(best_move==0)return alpha;
        pv.clear(); if(best_move)pv.set(best_move,best_child);
        if(tt_){Bound bound=best<=original?Upper:(best>=beta?Lower:Exact);int stored=best;if(stored>MateScore-128)stored+=ply;if(stored<-MateScore+128)stored-=ply;tt_->store(p.hash_key,depth,stored,bound,best_move);}
        return best;
    }
};
} // namespace ace
