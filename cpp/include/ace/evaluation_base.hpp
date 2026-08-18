#pragma once

#include "ace/core.hpp"
#include <array>
#include <cmath>

namespace ace {
inline int kind(Piece piece){return (static_cast<int>(piece)-1)%6+1;}
inline int color_of(Piece piece){return piece<=WhiteKing?0:1;}
inline int relative_rank(int square,int color){return color==0?square/8:7-square/8;}
inline int piece_value(Piece piece,bool endgame=false){constexpr int middle[7]={0,100,320,330,500,900,0};constexpr int ending[7]={0,100,310,340,520,900,0};return (endgame?ending:middle)[kind(piece)];}
inline int phase_weight(Piece piece){constexpr int weights[7]={0,0,1,1,2,4,0};return weights[kind(piece)];}
inline std::array<int,2> placement(Piece piece,int square){const int color=color_of(piece),type=kind(piece),rank=relative_rank(square,color),file=square%8;const int center=static_cast<int>(14-4*(std::abs(file-3.5)+std::abs(square/8-3.5)));if(type==1)return {rank*6+center/3,rank*10+center/4};if(type==2)return {center*2,center*2};if(type==3)return {center+rank,center+rank*2};if(type==4){const int seventh=rank==6?18:0;return {rank*2+seventh,rank*3+seventh};}if(type==5)return {center/2,center};const bool castled=rank==0&&(file==2||file==6);return {castled?25:-center,center*2};}
} // namespace ace
