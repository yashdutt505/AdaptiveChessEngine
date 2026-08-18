#pragma once

#include "ace/movegen.hpp"
#include "ace/evaluation_base.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

namespace ace {

inline int pawn_features(const Position& position, int color) {
    const Piece pawn = color == 0 ? WhitePawn : BlackPawn;
    const Piece enemy_pawn = color == 0 ? BlackPawn : WhitePawn;
    std::vector<int> pawns, enemies;
    for (int square = 0; square < 64; ++square) {
        if (position.board.squares[square] == pawn) pawns.push_back(square);
        if (position.board.squares[square] == enemy_pawn) enemies.push_back(square);
    }
    int score = 0;
    for (int file = 0; file < 8; ++file) {
        int count = 0; for (int square : pawns) if (square % 8 == file) ++count;
        score -= std::max(0, count - 1) * 14;
    }
    for (int square : pawns) {
        const int file = square % 8, rank = square / 8;
        bool neighbor_file = false, connected = false, enemy_ahead = false;
        for (int other : pawns) if (other != square) {
            if (std::abs(other % 8 - file) == 1) neighbor_file = true;
            if (std::abs(other % 8 - file) == 1 && std::abs(other / 8 - rank) <= 1) connected = true;
        }
        if (!neighbor_file) score -= 12;
        if (connected) score += 5;
        for (int other : enemies) {
            if (std::abs(other % 8 - file) <= 1
                && (color == 0 ? other / 8 > rank : other / 8 < rank)) enemy_ahead = true;
        }
        if (!enemy_ahead) { const int advance = relative_rank(square, color); score += 15 + advance * advance * 3; }
    }
    return score;
}

inline int slider_mobility(const Position& position, int square, int color, int begin, int end) {
    Bitboard attacks=begin==0&&end==8?queen_attacks(square,position.board.occupied):begin==0?bishop_attacks(square,position.board.occupied):rook_attacks(square,position.board.occupied);
    attacks&=~(color==0?position.board.white:position.board.black);return population_count(attacks);
}

inline int mobility(const Position& position, int color) {
    int score = 0;
    constexpr int knight_delta[8][2] = {{-2,-1},{-2,1},{-1,-2},{-1,2},{1,-2},{1,2},{2,-1},{2,1}};
    for (int square = 0; square < 64; ++square) {
        const Piece piece = position.board.squares[square];
        if (piece == (color == 0 ? WhiteKnight : BlackKnight)) {
            int count = 0;
            for (const auto& delta : knight_delta) {
                const int file = square % 8 + delta[0], rank = square / 8 + delta[1];
                if (file >= 0 && file < 8 && rank >= 0 && rank < 8
                    && !friendly(position.board.squares[rank * 8 + file], color)) ++count;
            }
            score += count * 4;
        } else if (piece == (color == 0 ? WhiteBishop : BlackBishop)) score += slider_mobility(position, square, color, 0, 4) * 3;
        else if (piece == (color == 0 ? WhiteRook : BlackRook)) score += slider_mobility(position, square, color, 4, 8) * 2;
        else if (piece == (color == 0 ? WhiteQueen : BlackQueen)) score += slider_mobility(position, square, color, 0, 8);
    }
    return score;
}

inline int rook_features(const Position& position, int color) {
    const Piece rook = color == 0 ? WhiteRook : BlackRook;
    const Piece pawn = color == 0 ? WhitePawn : BlackPawn;
    const Piece enemy_pawn = color == 0 ? BlackPawn : WhitePawn;
    int score = 0;
    for (int square = 0; square < 64; ++square) if (position.board.squares[square] == rook) {
        bool friendly_pawn = false, hostile_pawn = false;
        for (int rank = 0; rank < 8; ++rank) {
            const Piece target = position.board.squares[rank * 8 + square % 8];
            friendly_pawn |= target == pawn; hostile_pawn |= target == enemy_pawn;
        }
        if (!friendly_pawn) { score += 12; if (!hostile_pawn) score += 10; }
    }
    return score;
}

inline int king_safety(const Position& position, int color) {
    const int king = color == 0 ? position.white_king : position.black_king;
    const Piece pawn = color == 0 ? WhitePawn : BlackPawn;
    int score = 0;
    for (int df = -1; df <= 1; ++df) {
        const int file = king % 8 + df; if (file < 0 || file >= 8) continue;
        bool shielded = false;
        for (int distance = 1; distance <= 2; ++distance) {
            const int rank = king / 8 + (color == 0 ? distance : -distance);
            if (rank >= 0 && rank < 8 && position.board.squares[rank * 8 + file] == pawn) {
                score += distance == 1 ? 12 : 6; shielded = true; break;
            }
        }
        if (!shielded) score -= 10;
    }
    return score;
}

inline int finish_evaluation(const Position& position,int mg[2],int eg[2],const int bishops[2],int phase){
    for (int color = 0; color < 2; ++color) {
        const int structure = pawn_features(position, color), rooks = rook_features(position, color);
        const int pair = bishops[color] >= 2 ? 30 : 0, moves = mobility(position, color);
        mg[color] += structure + rooks + pair + moves + king_safety(position, color);
        eg[color] += structure + rooks + pair + moves / 2;
    }
    phase = std::min(phase, 24);const int score=((mg[0]-mg[1])*phase+(eg[0]-eg[1])*(24-phase))/24;return position.side_to_move==0?score:-score;
}

inline int evaluate_full(const Position& position) {
    int mg[2] = {0,0}, eg[2] = {0,0}, bishops[2] = {0,0}, phase = 0;
    for (int square = 0; square < 64; ++square) {
        const Piece piece = position.board.squares[square]; if (piece == Empty) continue;
        const int color = color_of(piece), type = kind(piece); const auto place = placement(piece, square);
        mg[color] += piece_value(piece) + place[0]; eg[color] += piece_value(piece, true) + place[1];
        phase += phase_weight(piece); if (type == 3) ++bishops[color];
    }
    return finish_evaluation(position,mg,eg,bishops,phase);
}

inline int evaluate(const Position& position){int mg[2]={position.mg_base[0],position.mg_base[1]},eg[2]={position.eg_base[0],position.eg_base[1]},bishops[2]={position.bishop_count[0],position.bishop_count[1]};return finish_evaluation(position,mg,eg,bishops,position.phase);}

}  // namespace ace
