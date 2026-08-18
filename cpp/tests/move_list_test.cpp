#include "ace/core.hpp"
#include <cassert>

int main(){ace::MoveList moves;for(unsigned index=0;index<218;++index)moves.push_back(index+1);assert(moves.size()==218&&moves[0]==1&&moves[217]==218);moves.erase(std::remove_if(moves.begin(),moves.end(),[](ace::Move move){return move%2==0;}),moves.end());assert(moves.size()==109);for(const auto move:moves)assert(move%2==1);}
