#pragma once

#include "ace/position.hpp"

#include <array>
#include <vector>

namespace ace {

inline bool is_white(Piece piece) { return piece >= WhitePawn && piece <= WhiteKing; }
inline bool is_black(Piece piece) { return piece >= BlackPawn && piece <= BlackKing; }
inline bool friendly(Piece piece, int color) { return color == 0 ? is_white(piece) : is_black(piece); }
inline bool enemy(Piece piece, int color) { return color == 0 ? is_black(piece) : is_white(piece); }

inline bool is_square_attacked(const Position& position, int square, int by_color) {
    const int target_file = square % 8;
    const int target_rank = square / 8;
    const Piece pawn = by_color == 0 ? WhitePawn : BlackPawn;
    const int pawn_rank = target_rank + (by_color == 0 ? -1 : 1);
    if (pawn_rank >= 0 && pawn_rank < 8) {
        for (int file : {target_file - 1, target_file + 1}) {
            if (file >= 0 && file < 8 && position.board.squares[pawn_rank * 8 + file] == pawn) return true;
        }
    }

    constexpr int knight_delta[8][2] = {
        {-2,-1},{-2,1},{-1,-2},{-1,2},{1,-2},{1,2},{2,-1},{2,1}
    };
    const Piece knight = by_color == 0 ? WhiteKnight : BlackKnight;
    for (const auto& delta : knight_delta) {
        const int file = target_file + delta[0];
        const int rank = target_rank + delta[1];
        if (file >= 0 && file < 8 && rank >= 0 && rank < 8
            && position.board.squares[rank * 8 + file] == knight) return true;
    }

    const Piece king = by_color == 0 ? WhiteKing : BlackKing;
    for (int df = -1; df <= 1; ++df) for (int dr = -1; dr <= 1; ++dr) {
        if (df == 0 && dr == 0) continue;
        const int file = target_file + df;
        const int rank = target_rank + dr;
        if (file >= 0 && file < 8 && rank >= 0 && rank < 8
            && position.board.squares[rank * 8 + file] == king) return true;
    }

    constexpr int directions[8][2] = {
        {-1,-1},{-1,1},{1,-1},{1,1},{-1,0},{1,0},{0,-1},{0,1}
    };
    const Piece bishop = by_color == 0 ? WhiteBishop : BlackBishop;
    const Piece rook = by_color == 0 ? WhiteRook : BlackRook;
    const Piece queen = by_color == 0 ? WhiteQueen : BlackQueen;
    for (int index = 0; index < 8; ++index) {
        int file = target_file + directions[index][0];
        int rank = target_rank + directions[index][1];
        while (file >= 0 && file < 8 && rank >= 0 && rank < 8) {
            const Piece piece = position.board.squares[rank * 8 + file];
            if (piece != Empty) {
                if (piece == queen || (index < 4 ? piece == bishop : piece == rook)) return true;
                break;
            }
            file += directions[index][0];
            rank += directions[index][1];
        }
    }
    return false;
}

inline bool in_check(const Position& position, int color) {
    const int king = color == 0 ? position.white_king : position.black_king;
    return is_square_attacked(position, king, color ^ 1);
}

inline void add_move(std::vector<Move>& moves, const Position& position,
    int from, int to, Piece piece, std::uint8_t flags = 0, Piece promotion = Empty) {
    const Piece captured = position.board.squares[to];
    if (captured != Empty) flags |= Capture;
    moves.push_back(encode_move(from, to, piece, captured, promotion, flags));
}

inline std::vector<Move> pseudo_legal_moves(const Position& position) {
    std::vector<Move> moves;
    moves.reserve(64);
    const int color = position.side_to_move;
    const Piece pawn = color == 0 ? WhitePawn : BlackPawn;
    const Piece enemy_pawn = color == 0 ? BlackPawn : WhitePawn;
    const int direction = color == 0 ? 1 : -1;
    const int start_rank = color == 0 ? 1 : 6;
    const int promotion_rank = color == 0 ? 7 : 0;

    for (int from = 0; from < 64; ++from) {
        const Piece piece = position.board.squares[from];
        if (!friendly(piece, color)) continue;
        const int source_file = from % 8;
        const int source_rank = from / 8;

        if (piece == pawn) {
            const int next_rank = source_rank + direction;
            if (next_rank < 0 || next_rank >= 8) continue;
            const int to = next_rank * 8 + source_file;
            if (position.board.squares[to] == Empty) {
                if (next_rank == promotion_rank) {
                    const Piece promotions[4] = {
                        color == 0 ? WhiteQueen : BlackQueen,
                        color == 0 ? WhiteRook : BlackRook,
                        color == 0 ? WhiteBishop : BlackBishop,
                        color == 0 ? WhiteKnight : BlackKnight,
                    };
                    for (Piece promoted : promotions) add_move(moves, position, from, to, piece, Promotion, promoted);
                } else {
                    add_move(moves, position, from, to, piece);
                    if (source_rank == start_rank) {
                        const int twice = (source_rank + 2 * direction) * 8 + source_file;
                        if (position.board.squares[twice] == Empty) {
                            add_move(moves, position, from, twice, piece, DoublePawnPush);
                        }
                    }
                }
            }
            for (int file : {source_file - 1, source_file + 1}) {
                if (file < 0 || file >= 8) continue;
                const int target = next_rank * 8 + file;
                const Piece captured = position.board.squares[target];
                if (enemy(captured, color) && captured != WhiteKing && captured != BlackKing) {
                    if (next_rank == promotion_rank) {
                        const Piece promotions[4] = {
                            color == 0 ? WhiteQueen : BlackQueen,
                            color == 0 ? WhiteRook : BlackRook,
                            color == 0 ? WhiteBishop : BlackBishop,
                            color == 0 ? WhiteKnight : BlackKnight,
                        };
                        for (Piece promoted : promotions) add_move(moves, position, from, target, piece, Promotion, promoted);
                    } else add_move(moves, position, from, target, piece);
                } else if (target == position.en_passant) {
                    const int captured_square = target + (color == 0 ? -8 : 8);
                    if (position.board.squares[captured_square] == enemy_pawn) {
                        moves.push_back(encode_move(from, target, piece, enemy_pawn, Empty, Capture | EnPassant));
                    }
                }
            }
            continue;
        }

        if (piece == (color == 0 ? WhiteKnight : BlackKnight)) {
            constexpr int deltas[8][2] = {
                {-2,-1},{-2,1},{-1,-2},{-1,2},{1,-2},{1,2},{2,-1},{2,1}
            };
            for (const auto& delta : deltas) {
                const int file = source_file + delta[0];
                const int rank = source_rank + delta[1];
                if (file < 0 || file >= 8 || rank < 0 || rank >= 8) continue;
                const int to = rank * 8 + file;
                const Piece target = position.board.squares[to];
                if (!friendly(target, color) && target != WhiteKing && target != BlackKing) add_move(moves, position, from, to, piece);
            }
            continue;
        }

        const bool bishop_like = piece == (color == 0 ? WhiteBishop : BlackBishop)
            || piece == (color == 0 ? WhiteQueen : BlackQueen);
        const bool rook_like = piece == (color == 0 ? WhiteRook : BlackRook)
            || piece == (color == 0 ? WhiteQueen : BlackQueen);
        constexpr int directions[8][2] = {
            {-1,-1},{-1,1},{1,-1},{1,1},{-1,0},{1,0},{0,-1},{0,1}
        };
        if (bishop_like || rook_like) {
            for (int index = 0; index < 8; ++index) {
                if ((index < 4 && !bishop_like) || (index >= 4 && !rook_like)) continue;
                int file = source_file + directions[index][0];
                int rank = source_rank + directions[index][1];
                while (file >= 0 && file < 8 && rank >= 0 && rank < 8) {
                    const int to = rank * 8 + file;
                    const Piece target = position.board.squares[to];
                    if (target == Empty) add_move(moves, position, from, to, piece);
                    else {
                        if (enemy(target, color) && target != WhiteKing && target != BlackKing) add_move(moves, position, from, to, piece);
                        break;
                    }
                    file += directions[index][0];
                    rank += directions[index][1];
                }
            }
            continue;
        }

        if (piece == (color == 0 ? WhiteKing : BlackKing)) {
            for (int df = -1; df <= 1; ++df) for (int dr = -1; dr <= 1; ++dr) {
                if (df == 0 && dr == 0) continue;
                const int file = source_file + df;
                const int rank = source_rank + dr;
                if (file < 0 || file >= 8 || rank < 0 || rank >= 8) continue;
                const int to = rank * 8 + file;
                const Piece target = position.board.squares[to];
                if (!friendly(target, color) && target != WhiteKing && target != BlackKing) add_move(moves, position, from, to, piece);
            }
        }
    }

    const int enemy_color = color ^ 1;
    const int king_from = color == 0 ? 4 : 60;
    const Piece king = color == 0 ? WhiteKing : BlackKing;
    const Piece rook = color == 0 ? WhiteRook : BlackRook;
    if (position.board.squares[king_from] == king
        && !is_square_attacked(position, king_from, enemy_color)) {
        const int king_right = color == 0 ? WhiteKingside : BlackKingside;
        const int queen_right = color == 0 ? WhiteQueenside : BlackQueenside;
        const int rook_king = color == 0 ? 7 : 63;
        const int rook_queen = color == 0 ? 0 : 56;
        if ((position.castling_rights & king_right) && position.board.squares[rook_king] == rook
            && position.board.squares[king_from + 1] == Empty && position.board.squares[king_from + 2] == Empty
            && !is_square_attacked(position, king_from + 1, enemy_color)
            && !is_square_attacked(position, king_from + 2, enemy_color)) {
            add_move(moves, position, king_from, king_from + 2, king, KingCastle);
        }
        if ((position.castling_rights & queen_right) && position.board.squares[rook_queen] == rook
            && position.board.squares[king_from - 1] == Empty && position.board.squares[king_from - 2] == Empty
            && position.board.squares[king_from - 3] == Empty
            && !is_square_attacked(position, king_from - 1, enemy_color)
            && !is_square_attacked(position, king_from - 2, enemy_color)) {
            add_move(moves, position, king_from, king_from - 2, king, QueenCastle);
        }
    }
    return moves;
}

inline std::vector<Move> legal_moves(Position& position) {
    const int color = position.side_to_move;
    std::vector<Move> legal;
    for (Move move : pseudo_legal_moves(position)) {
        position.make_move(move);
        if (!in_check(position, color)) legal.push_back(move);
        position.unmake_move();
    }
    return legal;
}

inline std::uint64_t perft(Position& position, int depth) {
    if (depth == 0) return 1;
    const std::vector<Move> moves = legal_moves(position);
    if (depth == 1) return moves.size();
    std::uint64_t nodes = 0;
    for (Move move : moves) {
        position.make_move(move);
        nodes += perft(position, depth - 1);
        position.unmake_move();
    }
    return nodes;
}

}  // namespace ace
