#pragma once

#include "ace/search.hpp"
#include <chrono>

namespace ace {
inline SearchResult aspiration_search(Position& position,Searcher& searcher,int depth,int previous_score,const SearchLimits& limits={},int initial_width=50,int* research_count=nullptr){
    const auto started=std::chrono::steady_clock::now();int alpha=std::max(-Infinity,previous_score-initial_width),beta=std::min(Infinity,previous_score+initial_width),width=initial_width;std::uint64_t total_nodes=0;int attempts=0;SearchResult result;
    while(true){
        SearchLimits attempt_limits=limits;if(limits.nodes!=std::numeric_limits<std::uint64_t>::max()){if(total_nodes>=limits.nodes){result.completed=false;break;}attempt_limits.nodes=limits.nodes-total_nodes;}
        result=searcher.search(position,depth,attempt_limits,alpha,beta);total_nodes+=result.nodes;++attempts;if(!result.completed)break;
        if(result.score<=alpha&&alpha>-Infinity){width=std::min(width*2,Infinity);alpha=std::max(-Infinity,alpha-width);continue;}
        if(result.score>=beta&&beta<Infinity){width=std::min(width*2,Infinity);beta=std::min(Infinity,beta+width);continue;}
        break;
    }
    result.nodes=total_nodes;result.time_ms=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-started).count();if(research_count)*research_count=std::max(0,attempts-1);return result;
}
} // namespace ace
