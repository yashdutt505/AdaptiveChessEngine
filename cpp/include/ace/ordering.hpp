#pragma once

#include "ace/evaluation.hpp"

#include <algorithm>
#include <array>
#include <utility>

namespace ace {
constexpr int MaxOrderingPly=128,MaxHistoryScore=1000000;

inline Bitboard attackers_to(int target,int color,const std::array<Bitboard,13>& pieces,Bitboard occupied){
    Bitboard attackers=0;const int file=target%8,rank=target/8;
    const Piece pawn=static_cast<Piece>((color?BlackPawn:WhitePawn));const int pawn_rank=rank+(color?1:-1);
    if(pawn_rank>=0&&pawn_rank<8)for(int pawn_file:{file-1,file+1})if(pawn_file>=0&&pawn_file<8)attackers|=pieces[pawn]&(Bitboard{1}<<(pawn_rank*8+pawn_file));
    constexpr int knight_delta[8][2]={{-2,-1},{-2,1},{-1,-2},{-1,2},{1,-2},{1,2},{2,-1},{2,1}};
    const Piece knight=static_cast<Piece>((color?BlackKnight:WhiteKnight));
    for(const auto& delta:knight_delta){const int f=file+delta[0],r=rank+delta[1];if(f>=0&&f<8&&r>=0&&r<8)attackers|=pieces[knight]&(Bitboard{1}<<(r*8+f));}
    const Piece king=static_cast<Piece>((color?BlackKing:WhiteKing));
    for(int df=-1;df<=1;++df)for(int dr=-1;dr<=1;++dr){const int f=file+df,r=rank+dr;if((df||dr)&&f>=0&&f<8&&r>=0&&r<8)attackers|=pieces[king]&(Bitboard{1}<<(r*8+f));}
    const Piece bishop=static_cast<Piece>((color?BlackBishop:WhiteBishop));const Piece rook=static_cast<Piece>((color?BlackRook:WhiteRook));const Piece queen=static_cast<Piece>((color?BlackQueen:WhiteQueen));
    attackers|=bishop_attacks(target,occupied)&(pieces[bishop]|pieces[queen]);attackers|=rook_attacks(target,occupied)&(pieces[rook]|pieces[queen]);
    return attackers;
}

inline std::pair<int,Piece> least_attacker(int target,int color,const std::array<Bitboard,13>& pieces,Bitboard occupied){
    const Bitboard attackers=attackers_to(target,color,pieces,occupied);
    for(int type=1;type<=6;++type){const Piece piece=static_cast<Piece>(type+(color?6:0));const Bitboard candidates=attackers&pieces[piece];if(candidates)for(int square=0;square<64;++square)if(candidates&(Bitboard{1}<<square))return {square,piece};}
    return {-1,Empty};
}

inline int recapture_gain(int target,int color,Piece occupant,std::array<Bitboard,13> pieces,Bitboard occupied){
    const auto attacker=least_attacker(target,color,pieces,occupied);if(attacker.first<0)return 0;
    const Bitboard source=Bitboard{1}<<attacker.first,target_mask=Bitboard{1}<<target;
    pieces[attacker.second]&=~source;pieces[occupant]&=~target_mask;pieces[attacker.second]|=target_mask;
    occupied=(occupied&~source)|target_mask;
    return std::max(0,piece_value(occupant)-recapture_gain(target,color^1,attacker.second,pieces,occupied));
}

inline int static_exchange_eval(const Position& position,Move move){
    const Piece captured=captured_piece(move);if(captured==Empty)return 0;
    auto pieces=position.board.pieces;Bitboard occupied=position.board.occupied;const int from=from_square(move),to=to_square(move);
    const Piece mover=moving_piece(move),placed=(move_flags(move)&Promotion)?promotion_piece(move):mover;
    const int capture_square=(move_flags(move)&EnPassant)?to+(position.side_to_move==0?-8:8):to;
    const Bitboard from_mask=Bitboard{1}<<from,to_mask=Bitboard{1}<<to,capture_mask=Bitboard{1}<<capture_square;
    pieces[mover]&=~from_mask;pieces[captured]&=~capture_mask;pieces[placed]|=to_mask;occupied&=~from_mask;occupied&=~capture_mask;occupied|=to_mask;
    return piece_value(captured)+piece_value(placed)-piece_value(mover)-recapture_gain(to,position.side_to_move^1,placed,pieces,occupied);
}

class SearchHeuristics {
    std::array<std::array<Move,2>,MaxOrderingPly> killers_{};
    std::array<std::array<std::array<int,64>,64>,2> history_{};
    std::array<std::array<Move,64>,64> countermoves_{};
public:
    int killer_rank(Move move,int ply)const{return ply<MaxOrderingPly?(move==killers_[ply][0]?2:move==killers_[ply][1]?1:0):0;}
    int history_score(Move move,int color)const{return history_[color][from_square(move)][to_square(move)];}
    bool is_countermove(Move move,Move previous)const{return previous&&countermoves_[from_square(previous)][to_square(previous)]==move;}
    void record_cutoff(Move move,int depth,int ply,int color,int move_index,Move previous,const MoveList& tried_quiets){
        if(move_flags(move)&(Capture|Promotion))return;
        if(ply<MaxOrderingPly&&move!=killers_[ply][0]){killers_[ply][1]=killers_[ply][0];killers_[ply][0]=move;}
        const int bonus=std::max(1,depth)*std::max(1,depth);auto& score=history_[color][from_square(move)][to_square(move)];score=std::min(MaxHistoryScore,score+bonus);
        if(previous)countermoves_[from_square(previous)][to_square(previous)]=move;
        for(const auto failed:tried_quiets){auto& value=history_[color][from_square(failed)][to_square(failed)];value=std::max(-MaxHistoryScore,value-bonus);}
        (void)move_index;
    }
};
} // namespace ace
