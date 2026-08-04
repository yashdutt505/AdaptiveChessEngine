#pragma once

#include "ace/movegen.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

namespace ace {

inline int kind(Piece piece) { return (static_cast<int>(piece) - 1) % 6 + 1; }
inline int color_of(Piece piece) { return piece <= WhiteKing ? 0 : 1; }
inline int relative_rank(int square, int color) { return color == 0 ? square / 8 : 7 - square / 8; }

inline int piece_value(Piece piece, bool endgame = false) {
    constexpr int middle[7] = {0, 100, 320, 330, 500, 900, 0};
    constexpr int ending[7] = {0, 100, 310, 340, 520, 900, 0};
    return (endgame ? ending : middle)[kind(piece)];
}

inline std::array<int, 2> placement(Piece piece, int square) {
    const int color = color_of(piece);
    const int type = kind(piece);
    const int rank = relative_rank(square, color);
    const int file = square % 8;
    const int center = static_cast<int>(14 - 4 * (std::abs(file - 3.5) + std::abs(square / 8 - 3.5)));
    if (type == 1) return {rank * 6 + center / 3, rank * 10 + center / 4};
    if (type == 2) return {center * 2, center * 2};
    if (type == 3) return {center + rank, center + rank * 2};
    if (type == 4) { const int seventh = rank == 6 ? 18 : 0; return {rank * 2 + seventh, rank * 3 + seventh}; }
    if (type == 5) return {center / 2, center};
    const bool castled = rank == 0 && (file == 2 || file == 6);
    return {castled ? 25 : -center, center * 2};
}

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
    constexpr int directions[8][2] = {{-1,-1},{-1,1},{1,-1},{1,1},{-1,0},{1,0},{0,-1},{0,1}};
    int mobility = 0;
    for (int index = begin; index < end; ++index) {
        int file = square % 8 + directions[index][0], rank = square / 8 + directions[index][1];
        while (file >= 0 && file < 8 && rank >= 0 && rank < 8) {
            const Piece target = position.board.squares[rank * 8 + file];
            if (friendly(target, color)) break;
            ++mobility;
            if (target != Empty) break;
            file += directions[index][0]; rank += directions[index][1];
        }
    }
    return mobility;
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

inline int evaluate(const Position& position) {
    int mg[2] = {0,0}, eg[2] = {0,0}, bishops[2] = {0,0}, phase = 0;
    constexpr int phase_weight[7] = {0,0,1,1,2,4,0};
    for (int square = 0; square < 64; ++square) {
        const Piece piece = position.board.squares[square]; if (piece == Empty) continue;
        const int color = color_of(piece), type = kind(piece); const auto place = placement(piece, square);
        mg[color] += piece_value(piece) + place[0]; eg[color] += piece_value(piece, true) + place[1];
        phase += phase_weight[type]; if (type == 3) ++bishops[color];
    }
    for (int color = 0; color < 2; ++color) {
        const int structure = pawn_features(position, color), rooks = rook_features(position, color);
        const int pair = bishops[color] >= 2 ? 30 : 0, moves = mobility(position, color);
        mg[color] += structure + rooks + pair + moves + king_safety(position, color);
        eg[color] += structure + rooks + pair + moves / 2;
    }
    phase = std::min(phase, 24);
    const int score = ((mg[0]-mg[1]) * phase + (eg[0]-eg[1]) * (24-phase)) / 24;
    return position.side_to_move == 0 ? score : -score;
}

}  // namespace ace
