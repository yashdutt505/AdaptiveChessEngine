#pragma once

#include "ace/core.hpp"
#include <array>
#include <vector>

namespace ace {

inline Bitboard ray_attacks(int square,Bitboard occupied,const int directions[][2],int count){
    Bitboard attacks=0;const int source_file=square%8,source_rank=square/8;
    for(int index=0;index<count;++index){int file=source_file+directions[index][0],rank=source_rank+directions[index][1];while(file>=0&&file<8&&rank>=0&&rank<8){const int target=rank*8+file;const Bitboard mask=Bitboard{1}<<target;attacks|=mask;if(occupied&mask)break;file+=directions[index][0];rank+=directions[index][1];}}
    return attacks;
}

inline Bitboard occupancy_index_mask(int square,const int directions[][2],int count){
    Bitboard mask=0;const int source_file=square%8,source_rank=square/8;
    for(int index=0;index<count;++index){int file=source_file+directions[index][0],rank=source_rank+directions[index][1];while(file>=0&&file<8&&rank>=0&&rank<8){const int next_file=file+directions[index][0],next_rank=rank+directions[index][1];if(next_file<0||next_file>=8||next_rank<0||next_rank>=8)break;mask|=Bitboard{1}<<(rank*8+file);file=next_file;rank=next_rank;}}
    return mask;
}

inline unsigned occupancy_index(Bitboard occupied,Bitboard mask){
    unsigned index=0,bit=0;while(mask){const Bitboard square=mask&(~mask+1);if(occupied&square)index|=1U<<bit;mask&=mask-1;++bit;}return index;
}

inline Bitboard occupancy_from_index(unsigned index,Bitboard mask){
    Bitboard occupied=0;unsigned bit=0;while(mask){const Bitboard square=mask&(~mask+1);if(index&(1U<<bit))occupied|=square;mask&=mask-1;++bit;}return occupied;
}

struct SlidingAttackTables {
    std::array<Bitboard,64> bishop_masks{},rook_masks{};
    std::array<std::vector<Bitboard>,64> bishop{},rook{};
    std::array<std::array<std::array<unsigned,256>,8>,64> bishop_index{},rook_index{};
    SlidingAttackTables(){
        constexpr int diagonals[4][2]={{-1,-1},{-1,1},{1,-1},{1,1}};
        constexpr int orthogonals[4][2]={{-1,0},{1,0},{0,-1},{0,1}};
        for(int square=0;square<64;++square){
            bishop_masks[square]=occupancy_index_mask(square,diagonals,4);rook_masks[square]=occupancy_index_mask(square,orthogonals,4);
            unsigned bishop_bits=0,rook_bits=0;for(Bitboard value=bishop_masks[square];value;value&=value-1)++bishop_bits;for(Bitboard value=rook_masks[square];value;value&=value-1)++rook_bits;
            bishop[square].resize(1U<<bishop_bits);rook[square].resize(1U<<rook_bits);
            for(unsigned byte=0;byte<8;++byte)for(unsigned value=0;value<256;++value){const Bitboard occupied=Bitboard{value}<<(byte*8);bishop_index[square][byte][value]=occupancy_index(occupied,bishop_masks[square]);rook_index[square][byte][value]=occupancy_index(occupied,rook_masks[square]);}
            for(unsigned index=0;index<bishop[square].size();++index){const Bitboard occupied=occupancy_from_index(index,bishop_masks[square]);bishop[square][index]=ray_attacks(square,occupied,diagonals,4);}
            for(unsigned index=0;index<rook[square].size();++index){const Bitboard occupied=occupancy_from_index(index,rook_masks[square]);rook[square][index]=ray_attacks(square,occupied,orthogonals,4);}
        }
    }
};

inline const SlidingAttackTables& sliding_tables(){static const SlidingAttackTables tables;return tables;}
inline unsigned byte_compressed_index(Bitboard occupied,const std::array<std::array<unsigned,256>,8>& map){return map[0][occupied&255]|map[1][(occupied>>8)&255]|map[2][(occupied>>16)&255]|map[3][(occupied>>24)&255]|map[4][(occupied>>32)&255]|map[5][(occupied>>40)&255]|map[6][(occupied>>48)&255]|map[7][(occupied>>56)&255];}
inline Bitboard bishop_attacks(int square,Bitboard occupied){const auto& tables=sliding_tables();return tables.bishop[square][byte_compressed_index(occupied,tables.bishop_index[square])];}
inline Bitboard rook_attacks(int square,Bitboard occupied){const auto& tables=sliding_tables();return tables.rook[square][byte_compressed_index(occupied,tables.rook_index[square])];}
inline Bitboard queen_attacks(int square,Bitboard occupied){return bishop_attacks(square,occupied)|rook_attacks(square,occupied);}

} // namespace ace
