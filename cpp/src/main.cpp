#include "ace/search.hpp"
#include <iostream>
#include <sstream>
#include <string>

namespace {
constexpr const char* StartFen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
std::string move_string(ace::Move move){std::string s=ace::square_to_string(ace::from_square(move))+ace::square_to_string(ace::to_square(move));if(ace::move_flags(move)&ace::Promotion){const int k=ace::kind(ace::promotion_piece(move));s+=k==5?'q':k==4?'r':k==3?'b':'n';}return s;}
ace::Move find_move(ace::Position& p,const std::string& text){for(auto move:ace::legal_moves(p))if(move_string(move)==text)return move;throw std::invalid_argument("illegal move");}
int uci_mate_score(int score){
    const int plies=ace::MateScore-std::abs(score);
    const int moves=(plies+1)/2;
    return score<0?-moves:moves;
}
}

int main(){
    ace::Position position; ace::load_fen(position,StartFen); ace::TranspositionTable tt(64); std::string line;
    while(std::getline(std::cin,line)){
        try{
            std::istringstream in(line);std::string command;in>>command;
            if(command=="uci"){std::cout<<"id name Adaptive Chess Engine C++\nid author Yash Dutt\noption name Hash type spin default 64 min 1 max 1024\noption name Clear Hash type button\nuciok\n"<<std::flush;}
            else if(command=="isready")std::cout<<"readyok\n"<<std::flush;
            else if(command=="ucinewgame"){ace::load_fen(position,StartFen);tt.clear();}
            else if(command=="setoption"){
                std::string token,name,value;in>>token;while(in>>token&&token!="value"){if(!name.empty())name+=' ';name+=token;}std::getline(in,value);if(!value.empty()&&value[0]==' ')value.erase(0,1);
                if(name=="Hash"&&!value.empty())tt.resize(static_cast<std::size_t>(std::stoul(value)));else if(name=="Clear Hash")tt.clear();
            }
            else if(command=="position"){
                std::string type;in>>type;std::string token;
                if(type=="startpos")ace::load_fen(position,StartFen);
                else if(type=="fen"){std::string fen,field;for(int i=0;i<6;++i){in>>field;if(i)fen+=' ';fen+=field;}ace::load_fen(position,fen);}
                if(in>>token){if(token!="moves")throw std::invalid_argument("expected moves");while(in>>token)position.make_move(find_move(position,token));}
            }
            else if(command=="go"){
                int max_depth=5;std::string token;while(in>>token)if(token=="depth")in>>max_depth;
                ace::SearchResult best;tt.new_search();
                for(int depth=1;depth<=max_depth;++depth){ace::Searcher searcher(&tt);best=searcher.search(position,depth);const bool mate=std::abs(best.score)>=ace::MateScore-1000;std::cout<<"info depth "<<depth<<" score "<<(mate?"mate ":"cp ")<<(mate?uci_mate_score(best.score):best.score)<<" nodes "<<best.nodes<<" time "<<best.time_ms<<" pv";for(auto move:best.pv)std::cout<<' '<<move_string(move);std::cout<<'\n'<<std::flush;}
                std::cout<<"bestmove "<<(best.best_move?move_string(best.best_move):"0000")<<'\n'<<std::flush;
            }
            else if(command=="quit")break;
        }catch(const std::exception& error){std::cout<<"info string error: "<<error.what()<<'\n'<<std::flush;}
    }
}
