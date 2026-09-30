#include "ace/adaptive_selector.hpp"

#include <array>
#include <cassert>
#include <cmath>

namespace {
void close(double actual,double expected,double tolerance=1e-12){assert(std::abs(actual-expected)<=tolerance);}

ace::Move find_move(ace::Position& position,const std::string& text){
    for(const auto move:ace::legal_moves(position)){
        std::string candidate=ace::square_to_string(ace::from_square(move))+ace::square_to_string(ace::to_square(move));
        if(candidate==text)return move;
    }
    assert(false);return 0;
}
}

int main(){
    const std::array<ace::OpponentErrorFeatures,4> fixtures{{
        {{{0,20,1,0,0,6400,16,0,0,0,0,0,0,10,0,1164,-832}}},
        {{{1,5,2,-300,300,2400,8,4,-20,-10,-15,0,2,35,1,1164,-832}}},
        {{{0,40,0,500,500,5000,12,1,30,10,20,2,0,20,0,1164,0}}},
        {{{0,12,4,-100,100,3200,10,2,-5,5,-10,-1,3,45,1,800,-300}}},
    }};
    const std::array<double,4> population{{0.10105107986916356,0.16205759195713296,0.1871531063094067,0.37248138581687895}};
    const std::array<double,4> personal{{0.13441645259856902,0.1953141790079501,0.1222325893022217,0.2808582154142871}};
    for(std::size_t index=0;index<fixtures.size();++index){
        close(ace::opponent_error_probability(ace::population_error_v1_model,fixtures[index]),population[index]);
        close(ace::opponent_error_probability(ace::personal_yashdutt7_lifetime_v1_model,fixtures[index]),personal[index]);
    }

    ace::Position position;
    ace::load_fen(position,"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    const auto features=ace::extract_opponent_error_features(position,find_move(position,"e2e4"));
    const std::array<double,17> python_reference{{0,20,0,0,0,6400,16,0,-23,22,5,-1,0,1,1,0,0}};
    assert(features.values==python_reference);
}
