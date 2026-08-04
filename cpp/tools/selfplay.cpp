#include "ace/strength.hpp"
#include <cstdlib>
#include <iostream>

int main(int argc,char** argv){
    const int games=argc>1?std::max(1,std::atoi(argv[1])):20;ace::SelfPlayConfig config;config.depth=argc>2?std::max(1,std::atoi(argv[2])):3;config.max_plies=argc>3?std::max(1,std::atoi(argv[3])):160;
    const ace::SearchOptions candidate{},baseline{false,false,false};ace::ScoreSprt sprt(0.0,10.0);int wins=0,draws=0,losses=0;
    for(int game=0;game<games;++game){
        const bool candidate_white=(game%2)==0;const auto result=candidate_white?ace::play_game(candidate,baseline,config):ace::play_game(baseline,candidate,config);
        const int candidate_result=candidate_white?result.outcome:-result.outcome;const double score=candidate_result>0?1.0:candidate_result<0?0.0:0.5;
        if(score==1.0)++wins;else if(score==0.0)++losses;else ++draws;const auto decision=sprt.record(score);
        std::cout<<"game "<<game+1<<" result "<<score<<" plies "<<result.moves.size()<<" llr "<<sprt.llr()<<'\n';
        if(decision!=ace::SprtDecision::Continue)break;
    }
    const char* decision=sprt.decision()==ace::SprtDecision::AcceptH1?"accept-h1":sprt.decision()==ace::SprtDecision::AcceptH0?"accept-h0":"continue";
    std::cout<<"summary wins "<<wins<<" draws "<<draws<<" losses "<<losses<<" games "<<sprt.games()<<" decision "<<decision<<" llr "<<sprt.llr()<<" bounds "<<sprt.lower_bound()<<' '<<sprt.upper_bound()<<'\n';
}
