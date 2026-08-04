#include "ace/transposition.hpp"
#include <cassert>
int main(){ ace::TranspositionTable tt(1); tt.store(42,5,30,ace::Exact,99); auto* e=tt.probe(42); assert(e&&e->depth==5&&e->move==99); tt.store(42,2,5,ace::Lower,1); assert(tt.probe(42)->depth==5); tt.new_search(); tt.store(42,2,5,ace::Lower,1); assert(tt.probe(42)->depth==2); tt.clear(); assert(!tt.probe(42)); }
