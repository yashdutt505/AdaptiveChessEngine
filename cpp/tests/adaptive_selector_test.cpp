#include "ace/adaptive_selector.hpp"

#include <cassert>

namespace {
ace::SearchResult candidate(ace::Move move,int score,const ace::PositionFeatures& features={}){
    ace::SearchResult result;result.best_move=move;result.score=score;result.depth=4;result.completed=true;result.features=features;return result;
}
ace::RootCandidatesResult completed(std::initializer_list<ace::SearchResult> candidates){
    ace::RootCandidatesResult result;result.candidates=candidates;result.completed=true;result.completed_depth=4;result.all_root_moves_searched=true;return result;
}
}

int main(){
    ace::PositionFeatures neutral_features,tactical_features;tactical_features.gives_check=1;tactical_features.legal_reply_count=10;
    const auto root=completed({candidate(1,100,neutral_features),candidate(2,80,tactical_features),candidate(3,64,tactical_features)});

    const auto neutral=ace::select_adaptive_root(root,ace::adaptive_profile_by_id("neutral-v1"));
    assert(neutral.selected_index==0&&!neutral.changed_move&&neutral.eligible_count==2);

    const auto tactical=ace::select_adaptive_root(root,ace::adaptive_profile_by_id("synthetic-tactical-pressure-v1"));
    assert(tactical.selected_index==1&&tactical.changed_move&&tactical.eligible_count==2&&tactical.utility>0);

    const auto wider=ace::select_adaptive_root(root,ace::adaptive_profile_by_id("synthetic-tactical-pressure-v1"),36);
    assert(wider.eligible_count==3);

    const auto population=ace::select_adaptive_root(root,ace::adaptive_profile_by_id("population-error-v1"));
    const auto personal=ace::select_adaptive_root(root,ace::adaptive_profile_by_id("personal-yashdutt7-lifetime-v1"));
    const auto random=ace::select_adaptive_root(root,ace::adaptive_profile_by_id("random-safe-v1"));
    assert(population.profile_evaluated&&personal.profile_evaluated&&random.profile_evaluated);
    assert(population.selected_index<2&&personal.selected_index<2&&random.selected_index<2);
    assert(std::abs(population.probability_bonus_cp)<=ace::LearnedMaximumBonusCp);
    assert(std::abs(personal.probability_bonus_cp)<=ace::LearnedMaximumBonusCp);

    auto incomplete=root;incomplete.completed=false;
    const auto fallback=ace::select_adaptive_root(incomplete,ace::adaptive_profile_by_id("synthetic-tactical-pressure-v1"));
    assert(fallback.selected_index==0&&!fallback.profile_evaluated&&!fallback.changed_move);

    const auto mate=completed({candidate(1,ace::MateScore-3,neutral_features),candidate(2,ace::MateScore-5,tactical_features)});
    const auto protected_mate=ace::select_adaptive_root(mate,ace::adaptive_profile_by_id("synthetic-tactical-pressure-v1"));
    assert(protected_mate.selected_index==0&&!protected_mate.profile_evaluated);

    auto invalid=ace::adaptive_profile_by_id("neutral-v1");invalid.weights[0]=1001;
    assert(!ace::select_adaptive_root(root,invalid).profile_evaluated);
    bool unknown=false;try{ace::adaptive_profile_by_id("missing");}catch(const std::invalid_argument&){unknown=true;}assert(unknown);
}
