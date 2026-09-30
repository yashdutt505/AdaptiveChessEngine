#pragma once

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

namespace ace {

constexpr std::size_t OpponentErrorFeatureCount=17;

struct OpponentErrorFeatures {std::array<double,OpponentErrorFeatureCount> values{};};

struct OpponentErrorNode {
    std::int64_t feature=0;
    double threshold=0.0;
    std::uint32_t left=0;
    std::uint32_t right=0;
    std::uint8_t missing_go_left=0;
    std::uint8_t leaf=0;
    double value=0.0;
};

struct OpponentErrorModel {
    const char* id=nullptr;
    double baseline=0.0;
    const OpponentErrorNode* nodes=nullptr;
    std::size_t node_count=0;
    const std::uint32_t* roots=nullptr;
    std::size_t tree_count=0;
};

inline double opponent_error_probability(const OpponentErrorModel& model,const OpponentErrorFeatures& features){
    double raw=model.baseline;
    for(std::size_t tree=0;tree<model.tree_count;++tree){
        std::uint32_t index=model.roots[tree];
        while(true){
            if(index>=model.node_count)throw std::runtime_error("invalid opponent error tree");
            const auto& node=model.nodes[index];
            if(node.leaf){raw+=node.value;break;}
            if(node.feature<0||static_cast<std::size_t>(node.feature)>=OpponentErrorFeatureCount)
                throw std::runtime_error("invalid opponent error feature index");
            const double value=features.values[static_cast<std::size_t>(node.feature)];
            index=std::isnan(value)?(node.missing_go_left?node.left:node.right):(value<=node.threshold?node.left:node.right);
        }
    }
    if(raw>=0.0){const double inverse=std::exp(-raw);return 1.0/(1.0+inverse);}
    const double exponential=std::exp(raw);return exponential/(1.0+exponential);
}

} // namespace ace
