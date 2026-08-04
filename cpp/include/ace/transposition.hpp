#pragma once

#include "ace/core.hpp"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace ace {
enum Bound : std::uint8_t { Exact, Lower, Upper };
struct TTEntry { std::uint64_t key=0; Move move=0; std::int32_t score=0; std::int16_t depth=-1; std::uint8_t generation=0; Bound bound=Exact; };

class TranspositionTable {
    static constexpr std::size_t Cluster = 4;
    std::vector<TTEntry> entries_;
    std::size_t buckets_ = 1;
public:
    std::uint8_t generation = 0;
    explicit TranspositionTable(std::size_t mb=16) { resize(mb); }
    void resize(std::size_t mb) {
        const std::size_t count = std::max<std::size_t>(Cluster, mb*1024*1024/sizeof(TTEntry));
        buckets_ = std::max<std::size_t>(1, count/Cluster); entries_.assign(buckets_*Cluster, {});
    }
    void clear() { std::fill(entries_.begin(), entries_.end(), TTEntry{}); generation=0; }
    void new_search() { ++generation; }
    TTEntry* probe(std::uint64_t key) {
        TTEntry* cluster=&entries_[(key%buckets_)*Cluster];
        for(std::size_t i=0;i<Cluster;++i) if(cluster[i].depth>=0 && cluster[i].key==key) return &cluster[i];
        return nullptr;
    }
    void store(std::uint64_t key,int depth,int score,Bound bound,Move move) {
        TTEntry* cluster=&entries_[(key%buckets_)*Cluster]; TTEntry* target=nullptr;
        for(std::size_t i=0;i<Cluster;++i) {
            if(cluster[i].depth>=0 && cluster[i].key==key) { if(cluster[i].generation==generation && cluster[i].depth>depth) return; target=&cluster[i]; break; }
            if(cluster[i].depth<0) { target=&cluster[i]; break; }
        }
        if(!target) target=&*std::min_element(cluster,cluster+Cluster,[this](const TTEntry&a,const TTEntry&b){
            const int av=(a.generation==generation?1000:0)+a.depth*4+(a.bound==Exact);
            const int bv=(b.generation==generation?1000:0)+b.depth*4+(b.bound==Exact); return av<bv;
        });
        *target=TTEntry{key,move,score,static_cast<std::int16_t>(depth),generation,bound};
    }
    int hashfull() const { const std::size_t n=std::min<std::size_t>(1000,entries_.size()); std::size_t used=0; for(std::size_t i=0;i<n;++i) used+=entries_[i].depth>=0&&entries_[i].generation==generation; return static_cast<int>(used*1000/n); }
};
} // namespace ace
