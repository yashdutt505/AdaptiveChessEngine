#pragma once

#include <algorithm>
#include <cstdint>

namespace ace {

inline int allocate_time_ms(int remaining_ms,int increment_ms,int moves_to_go,int overhead_ms) {
    if(remaining_ms<=0) return 1;
    const int usable=std::max(1,remaining_ms-std::max(0,overhead_ms));
    const int horizon=moves_to_go>0?moves_to_go:30;
    const int budget=usable/horizon+(increment_ms*3)/4;
    return std::max(1,std::min(budget,std::max(1,usable/2)));
}

} // namespace ace
