#include "ace/adaptive_features.hpp"

#include <algorithm>
#include <cassert>
#include <stdexcept>

namespace {
ace::Move named(ace::Position& position,const char* text){
    for(const auto move:ace::legal_moves(position))if(ace::square_to_string(ace::from_square(move))+ace::square_to_string(ace::to_square(move))==text)return move;
    return 0;
}
}

int main(){
    ace::Position start;ace::load_fen(start,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    const auto fen=ace::to_fen(start);const auto hash=start.hash_key;const auto history=start.history.size();
    const auto e4=ace::extract_position_features(start,named(start,"e2e4"));
    const auto e4_again=ace::extract_position_features(start,named(start,"e2e4"));
    assert(e4==e4_again&&e4.irreversible==1&&e4.castles==0&&e4.capture_value_cp==0&&e4.promotion_gain_cp==0);
    assert(e4.remaining_pawn_count==16&&e4.remaining_non_pawn_material_cp==6400&&e4.open_file_count==0&&e4.legal_reply_count==20);
    assert(ace::to_fen(start)==fen&&start.hash_key==hash&&start.history.size()==history);

    const auto knight=ace::extract_position_features(start,named(start,"g1f3"));assert(knight.irreversible==0);

    ace::Position capture;ace::load_fen(capture,"q6k/8/8/8/8/8/8/R5K1 w - - 0 1");
    const auto takes_queen=ace::extract_position_features(capture,named(capture,"a1a8"));
    assert(takes_queen.capture_value_cp==900&&takes_queen.irreversible==1&&takes_queen.material_balance_cp==500);

    bool rejected=false;try{ace::extract_position_features(start,ace::encode_move(0,1,ace::WhiteRook));}catch(const std::invalid_argument&){rejected=true;}
    assert(rejected&&ace::to_fen(start)==fen&&start.hash_key==hash);
}
