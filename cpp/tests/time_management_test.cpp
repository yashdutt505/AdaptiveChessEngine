#include "ace/time_management.hpp"
#include <cassert>

int main(){
    assert(ace::allocate_time_ms(60000,0,30,50)==1998);
    assert(ace::allocate_time_ms(1000,100,10,50)==170);
    assert(ace::allocate_time_ms(20,0,30,50)==1);
    assert(ace::allocate_time_ms(60000,0,1,50)==29975);
}
