#pragma once

#include "ace/search.hpp"

#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace ace {

constexpr std::size_t AdaptiveFeatureCount=16;
constexpr int DefaultAdaptiveLossBoundCp=35;

struct AdaptiveProfile {
    std::string id="neutral-v1";
    std::array<int,AdaptiveFeatureCount> weights{};
    std::array<int,AdaptiveFeatureCount> confidence{};
};

struct AdaptiveSelection {
    std::size_t selected_index=0;
    std::size_t eligible_count=0;
    std::int64_t utility=0;
    bool profile_evaluated=false;
    bool changed_move=false;
};

inline std::array<int,AdaptiveFeatureCount> feature_values(const PositionFeatures& f){
    return {f.capture_value_cp,f.promotion_gain_cp,f.gives_check,f.legal_reply_count,
        f.material_balance_cp,f.material_imbalance_cp,f.remaining_non_pawn_material_cp,
        f.remaining_pawn_count,f.open_file_count,f.mobility_balance,f.king_safety_balance,
        f.pawn_structure_balance,f.center_control_balance,f.pawn_tension_count,
        f.irreversible,f.castles};
}

constexpr std::array<int,AdaptiveFeatureCount> AdaptiveFeatureScales={
    900,800,1,40,900,900,6400,16,8,100,60,200,4,8,1,1
};

inline bool valid_profile(const AdaptiveProfile& profile){
    for(std::size_t i=0;i<AdaptiveFeatureCount;++i)
        if(profile.weights[i]<-1000||profile.weights[i]>1000||profile.confidence[i]<0||profile.confidence[i]>1000)return false;
    return true;
}

inline bool mate_score(int score){return std::abs(score)>=MateScore-1000;}

inline AdaptiveSelection select_adaptive_root(const RootCandidatesResult& root,const AdaptiveProfile& profile,int loss_bound_cp=DefaultAdaptiveLossBoundCp){
    AdaptiveSelection selection;
    if(loss_bound_cp<0||!valid_profile(profile)||!root.completed||root.completed_depth<1||!root.all_root_moves_searched||root.candidates.empty())return selection;
    const auto& neutral=root.candidates.front();
    if(!neutral.completed)return selection;
    selection.eligible_count=1;
    if(mate_score(neutral.score))return selection;
    const auto baseline=feature_values(neutral.features);std::int64_t best_utility=0;selection.profile_evaluated=true;
    for(std::size_t index=1;index<root.candidates.size();++index){
        const auto& candidate=root.candidates[index];
        if(!candidate.completed||neutral.score-candidate.score>loss_bound_cp||candidate.score<=-MateScore+1000)continue;
        ++selection.eligible_count;const auto values=feature_values(candidate.features);std::int64_t utility=0;
        for(std::size_t feature=0;feature<AdaptiveFeatureCount;++feature){
            const auto normalized=std::max(-1000,std::min(1000,(values[feature]-baseline[feature])*1000/AdaptiveFeatureScales[feature]));
            utility+=static_cast<std::int64_t>(normalized)*profile.weights[feature]*profile.confidence[feature];
        }
        if(utility>best_utility){best_utility=utility;selection.selected_index=index;}
    }
    selection.utility=best_utility;selection.changed_move=selection.selected_index!=0;return selection;
}

inline AdaptiveProfile adaptive_profile_by_id(const std::string& id){
    AdaptiveProfile profile;profile.id=id;
    const auto set=[&](std::size_t index,int weight){profile.weights[index]=weight;profile.confidence[index]=1000;};
    if(id=="neutral-v1")return profile;
    if(id=="synthetic-tactical-pressure-v1"){
        set(0,650);set(1,400);set(2,900);set(3,-500);set(5,450);set(6,250);set(8,350);set(12,300);set(13,250);set(14,200);
    }else if(id=="synthetic-simplification-pressure-v1"){
        set(0,700);set(3,-150);set(4,500);set(5,-250);set(6,-900);set(7,-350);set(10,400);set(13,-500);set(14,300);
    }else if(id=="synthetic-complexity-pressure-v1"){
        set(3,450);set(5,600);set(6,850);set(7,300);set(8,250);set(9,350);set(13,750);set(14,450);
    }else if(id=="synthetic-positional-restriction-v1"){
        set(3,-550);set(4,250);set(9,800);set(10,650);set(11,700);set(12,850);set(13,-200);set(15,350);
    }else throw std::invalid_argument("unknown adaptive profile");
    return profile;
}

} // namespace ace
