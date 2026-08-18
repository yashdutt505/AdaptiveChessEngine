#include "ace/search.hpp"
#include "ace/iterative.hpp"
#include "ace/time_management.hpp"

#include <atomic>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <thread>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace {
constexpr const char* StartFen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

struct GoParameters {
    int depth=64,movetime=-1,mate=0,wtime=-1,btime=-1,winc=0,binc=0,movestogo=0;
    std::uint64_t nodes=std::numeric_limits<std::uint64_t>::max();
    bool infinite=false;
};

std::string move_string(ace::Move move){
    std::string text=ace::square_to_string(ace::from_square(move))+ace::square_to_string(ace::to_square(move));
    if(ace::move_flags(move)&ace::Promotion){const int kind=ace::kind(ace::promotion_piece(move));text+=kind==5?'q':kind==4?'r':kind==3?'b':'n';}
    return text;
}

ace::Move find_move(ace::Position& position,const std::string& text){
    for(const auto move:ace::legal_moves(position))if(move_string(move)==text)return move;
    throw std::invalid_argument("illegal move");
}

int uci_mate_score(int score){const int moves=(ace::MateScore-std::abs(score)+1)/2;return score<0?-moves:moves;}

GoParameters parse_go(std::istringstream& input){
    GoParameters parameters;std::string token;
    while(input>>token){
        if(token=="depth")input>>parameters.depth;else if(token=="movetime")input>>parameters.movetime;
        else if(token=="nodes")input>>parameters.nodes;else if(token=="mate")input>>parameters.mate;
        else if(token=="wtime")input>>parameters.wtime;else if(token=="btime")input>>parameters.btime;
        else if(token=="winc")input>>parameters.winc;else if(token=="binc")input>>parameters.binc;
        else if(token=="movestogo")input>>parameters.movestogo;else if(token=="infinite")parameters.infinite=true;
    }
    return parameters;
}

void print_info(const ace::SearchResult& result,int depth,std::uint64_t nodes,long long elapsed,int multipv=0){
    const bool mate=std::abs(result.score)>=ace::MateScore-1000;
    std::cout<<"info depth "<<depth;
    if(multipv>0)std::cout<<" multipv "<<multipv;
    std::cout<<" score "<<(mate?"mate ":"cp ")<<(mate?uci_mate_score(result.score):result.score)<<" nodes "<<nodes<<" time "<<elapsed<<" pv";
    for(const auto move:result.pv)std::cout<<' '<<move_string(move);
    std::cout<<'\n'<<std::flush;
}

void run_search(ace::Position position,ace::TranspositionTable& table,GoParameters parameters,int move_overhead,int multipv,std::atomic<bool>& stop){
    if(parameters.mate>0)parameters.depth=std::min(parameters.depth,parameters.mate*2);
    if(parameters.movetime<0&&!parameters.infinite){
        const int clock=position.side_to_move==0?parameters.wtime:parameters.btime;
        const int increment=position.side_to_move==0?parameters.winc:parameters.binc;
        if(clock>=0)parameters.movetime=ace::allocate_time_ms(clock,increment,parameters.movestogo,move_overhead);
    }
    const auto started=std::chrono::steady_clock::now();
    const auto deadline=parameters.movetime>=0?started+std::chrono::milliseconds(std::max(1,parameters.movetime)):std::chrono::steady_clock::time_point::max();
    auto legal=ace::legal_moves(position);ace::SearchResult best;if(!legal.empty())best.best_move=legal.front();
    std::uint64_t total_nodes=0;table.new_search();ace::Searcher searcher(&table);bool has_previous=false;int previous_score=0;
    for(int depth=1;depth<=parameters.depth&&!stop.load(std::memory_order_relaxed);++depth){
        ace::SearchLimits limits;limits.deadline=deadline;limits.stop=&stop;
        limits.nodes=parameters.nodes==std::numeric_limits<std::uint64_t>::max()?parameters.nodes:parameters.nodes-total_nodes;
        if(multipv>1){
            auto result=searcher.search_root_candidates(position,depth,static_cast<std::size_t>(multipv),limits);total_nodes+=result.nodes;
            if(!result.completed||result.candidates.empty())break;
            best=result.candidates.front();previous_score=best.score;has_previous=true;
            const auto elapsed=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-started).count();
            for(std::size_t index=0;index<result.candidates.size();++index)print_info(result.candidates[index],depth,total_nodes,elapsed,static_cast<int>(index+1));
        }else{
            auto result=has_previous?ace::aspiration_search(position,searcher,depth,previous_score,limits):searcher.search(position,depth,limits);total_nodes+=result.nodes;
            if(!result.completed)break;
            best=result;previous_score=best.score;has_previous=true;
            const auto elapsed=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-started).count();print_info(best,depth,total_nodes,elapsed);
        }
        const bool mate=std::abs(best.score)>=ace::MateScore-1000;
        if(total_nodes>=parameters.nodes||(mate&&parameters.mate>0))break;
    }
    std::cout<<"bestmove "<<(best.best_move?move_string(best.best_move):"0000")<<'\n'<<std::flush;
}

class SearchWorker {
    struct Task {ace::Position position;ace::TranspositionTable* table;GoParameters parameters;int overhead,multipv;std::atomic<bool>* stop;};
#ifdef _WIN32
    HANDLE handle_=nullptr;
    static DWORD WINAPI entry(void* raw){std::unique_ptr<Task> task(static_cast<Task*>(raw));run_search(std::move(task->position),*task->table,task->parameters,task->overhead,task->multipv,*task->stop);return 0;}
#else
    std::thread thread_;
#endif
public:
    bool joinable() const {
#ifdef _WIN32
        return handle_!=nullptr;
#else
        return thread_.joinable();
#endif
    }
    void start(ace::Position position,ace::TranspositionTable& table,GoParameters parameters,int overhead,int multipv,std::atomic<bool>& stop){
        auto* task=new Task{std::move(position),&table,parameters,overhead,multipv,&stop};
#ifdef _WIN32
        handle_=CreateThread(nullptr,0,entry,task,0,nullptr);if(!handle_){delete task;throw std::runtime_error("could not start search thread");}
#else
        thread_=std::thread([task](){std::unique_ptr<Task> owned(task);run_search(std::move(owned->position),*owned->table,owned->parameters,owned->overhead,owned->multipv,*owned->stop);});
#endif
    }
    void join(){
#ifdef _WIN32
        WaitForSingleObject(handle_,INFINITE);CloseHandle(handle_);handle_=nullptr;
#else
        thread_.join();
#endif
    }
};
} // namespace

int main(){
    ace::Position position;ace::load_fen(position,StartFen);ace::TranspositionTable table(64);
    int move_overhead=50,multipv=1;std::atomic<bool> stop{false};SearchWorker worker;std::string line;
    const auto stop_search=[&](){if(worker.joinable()){stop.store(true,std::memory_order_relaxed);worker.join();}stop.store(false,std::memory_order_relaxed);};
    while(std::getline(std::cin,line)){
        try{
            std::istringstream input(line);std::string command;input>>command;
            if(command=="uci")std::cout<<"id name Adaptive Chess Engine C++\nid author Yash Dutt\noption name Hash type spin default 64 min 1 max 1024\noption name Clear Hash type button\noption name Move Overhead type spin default 50 min 0 max 5000\noption name MultiPV type spin default 1 min 1 max 16\nuciok\n"<<std::flush;
            else if(command=="isready")std::cout<<"readyok\n"<<std::flush;
            else if(command=="stop")stop_search();
            else if(command=="quit"){stop_search();break;}
            else if(command=="ucinewgame"){stop_search();ace::load_fen(position,StartFen);table.clear();}
            else if(command=="setoption"){
                stop_search();std::string token,name,value;input>>token;
                while(input>>token&&token!="value"){if(!name.empty())name+=' ';name+=token;}std::getline(input,value);if(!value.empty()&&value[0]==' ')value.erase(0,1);
                if(name=="Hash"&&!value.empty())table.resize(static_cast<std::size_t>(std::stoul(value)));else if(name=="Clear Hash")table.clear();else if(name=="Move Overhead"&&!value.empty())move_overhead=std::max(0,std::min(std::stoi(value),5000));else if(name=="MultiPV"&&!value.empty())multipv=std::max(1,std::min(std::stoi(value),16));
            }else if(command=="position"){
                stop_search();std::string type,token;input>>type;
                if(type=="startpos")ace::load_fen(position,StartFen);
                else if(type=="fen"){std::string fen,field;for(int index=0;index<6;++index){input>>field;if(index)fen+=' ';fen+=field;}ace::load_fen(position,fen);}
                if(input>>token){if(token!="moves")throw std::invalid_argument("expected moves");while(input>>token)position.make_move(find_move(position,token));}
            }else if(command=="go"){
                stop_search();const auto parameters=parse_go(input);const auto snapshot=position;
                worker.start(snapshot,table,parameters,move_overhead,multipv,stop);
            }
        }catch(const std::exception& error){std::cout<<"info string error: "<<error.what()<<'\n'<<std::flush;}
    }
    stop_search();
}
