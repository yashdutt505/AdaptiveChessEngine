#pragma once

#include "ace/evaluation.hpp"

#include <algorithm>
#include <stdexcept>

namespace ace {

// Profile-independent measurements of the position reached by one legal root
// move. Balance fields are expressed from the root mover's point of view.
struct PositionFeatures {
    int capture_value_cp=0;
    int promotion_gain_cp=0;
    int gives_check=0;
    int legal_reply_count=0;
    int material_balance_cp=0;
    int material_imbalance_cp=0;
    int remaining_non_pawn_material_cp=0;
    int remaining_pawn_count=0;
    int open_file_count=0;
    int mobility_balance=0;
    int king_safety_balance=0;
    int pawn_structure_balance=0;
    int center_control_balance=0;
    int pawn_tension_count=0;
    int irreversible=0;
    int castles=0;

    bool operator==(const PositionFeatures& other)const{
        return capture_value_cp==other.capture_value_cp&&promotion_gain_cp==other.promotion_gain_cp
            &&gives_check==other.gives_check&&legal_reply_count==other.legal_reply_count
            &&material_balance_cp==other.material_balance_cp&&material_imbalance_cp==other.material_imbalance_cp
            &&remaining_non_pawn_material_cp==other.remaining_non_pawn_material_cp&&remaining_pawn_count==other.remaining_pawn_count
            &&open_file_count==other.open_file_count&&mobility_balance==other.mobility_balance
            &&king_safety_balance==other.king_safety_balance&&pawn_structure_balance==other.pawn_structure_balance
            &&center_control_balance==other.center_control_balance&&pawn_tension_count==other.pawn_tension_count
            &&irreversible==other.irreversible&&castles==other.castles;
    }
};

inline int material_for(const Position& position,int color,bool include_pawns=true){
    int total=0;
    for(int square=0;square<64;++square){
        const Piece piece=position.board.squares[square];
        if(piece==Empty||color_of(piece)!=color||kind(piece)==6||(!include_pawns&&kind(piece)==1))continue;
        total+=piece_value(piece);
    }
    return total;
}

inline int open_files(const Position& position){
    int total=0;
    for(int file=0;file<8;++file){
        bool pawn=false;
        for(int rank=0;rank<8;++rank){const Piece piece=position.board.squares[rank*8+file];pawn|=kind(piece)==1;}
        if(!pawn)++total;
    }
    return total;
}

inline int center_control(const Position& position,int color){
    int total=0;
    for(const int square:{27,28,35,36})if(is_square_attacked(position,square,color))++total;
    return total;
}

inline int pawn_tensions(const Position& position){
    int total=0;
    for(int square=0;square<64;++square){
        const Piece piece=position.board.squares[square];if(piece!=WhitePawn)continue;
        const int rank=square/8,file=square%8,target_rank=rank+1;if(target_rank>=8)continue;
        for(const int target_file:{file-1,file+1})if(target_file>=0&&target_file<8&&position.board.squares[target_rank*8+target_file]==BlackPawn)++total;
    }
    return total;
}

inline PositionFeatures extract_position_features(Position& position,Move move){
    const auto legal=legal_moves(position);
    if(std::find(legal.begin(),legal.end(),move)==legal.end())throw std::invalid_argument("feature extraction requires a legal move");
    const int mover=position.side_to_move;PositionFeatures features;
    features.capture_value_cp=piece_value(captured_piece(move));
    features.promotion_gain_cp=has_flag(move,Promotion)?piece_value(promotion_piece(move))-piece_value(moving_piece(move)):0;
    features.irreversible=(kind(moving_piece(move))==1||has_flag(move,Capture)||has_flag(move,Promotion))?1:0;
    features.castles=(has_flag(move,KingCastle)||has_flag(move,QueenCastle))?1:0;

    position.make_move(move);const int opponent=mover^1;
    features.gives_check=in_check(position,opponent)?1:0;
    features.legal_reply_count=static_cast<int>(legal_moves(position).size());
    const int mover_material=material_for(position,mover),opponent_material=material_for(position,opponent);
    features.material_balance_cp=mover_material-opponent_material;
    features.material_imbalance_cp=std::abs(features.material_balance_cp);
    features.remaining_non_pawn_material_cp=material_for(position,0,false)+material_for(position,1,false);
    features.remaining_pawn_count=population_count(position.board.pieces[WhitePawn]|position.board.pieces[BlackPawn]);
    features.open_file_count=open_files(position);
    features.mobility_balance=mobility(position,mover)-mobility(position,opponent);
    features.king_safety_balance=king_safety(position,mover)-king_safety(position,opponent);
    features.pawn_structure_balance=pawn_features(position,mover)-pawn_features(position,opponent);
    features.center_control_balance=center_control(position,mover)-center_control(position,opponent);
    features.pawn_tension_count=pawn_tensions(position);
    position.unmake_move();return features;
}

} // namespace ace
