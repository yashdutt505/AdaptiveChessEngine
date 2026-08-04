#include "ace/strength.hpp"
#include <cassert>

int main(){
    ace::ScoreSprt winning(0,10);for(int index=0;index<1000&&winning.decision()==ace::SprtDecision::Continue;++index)winning.record(1.0);assert(winning.decision()==ace::SprtDecision::AcceptH1);
    ace::ScoreSprt losing(0,10);for(int index=0;index<1000&&losing.decision()==ace::SprtDecision::Continue;++index)losing.record(0.0);assert(losing.decision()==ace::SprtDecision::AcceptH0);
    ace::SelfPlayConfig config;config.depth=2;config.max_plies=8;const auto first=ace::play_game({}, {},config);const auto second=ace::play_game({}, {},config);assert(first.moves==second.moves&&first.final_fen==second.final_fen&&first.moves.size()==8);
    ace::Position replay;ace::load_fen(replay,ace::StandardStartFen);for(const auto move:first.moves){bool found=false;for(const auto legal:ace::legal_moves(replay))if(legal==move){found=true;break;}assert(found);replay.make_move(move);}assert(replay.board.valid()&&ace::to_fen(replay)==first.final_fen);
    const auto mate=ace::play_game({}, {},config,"7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - 0 1");assert(!mate.moves.empty()&&mate.outcome==1);
}
