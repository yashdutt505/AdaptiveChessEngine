#pragma once

#include "ace/core.hpp"
#include "ace/zobrist_keys.hpp"

#include <cctype>
#include <sstream>
#include <stdexcept>
#include <string>

namespace ace {

constexpr int NoEnPassant = -1;
constexpr int WhiteKingside = 1;
constexpr int WhiteQueenside = 2;
constexpr int BlackKingside = 4;
constexpr int BlackQueenside = 8;

inline Piece piece_from_char(char value) {
    constexpr const char* symbols = ".PNBRQKpnbrqk";
    for (int piece = WhitePawn; piece <= BlackKing; ++piece) {
        if (symbols[piece] == value) return static_cast<Piece>(piece);
    }
    throw std::invalid_argument("Unknown FEN piece");
}

inline char piece_to_char(Piece piece) {
    constexpr const char* symbols = ".PNBRQKpnbrqk";
    return symbols[piece];
}

struct Position {
    Board board;
    int side_to_move = 0;
    int castling_rights = 0;
    int en_passant = NoEnPassant;
    int halfmove_clock = 0;
    int fullmove_number = 1;
    int white_king = -1;
    int black_king = -1;
    std::uint64_t hash_key = 0;

    void clear() { *this = Position{}; }

    void add_piece(int square, Piece piece) {
        board.add(square, piece);
        if (piece == WhiteKing) white_king = square;
        if (piece == BlackKing) black_king = square;
    }
};

inline std::uint64_t compute_hash(const Position& position) {
    std::uint64_t key = zobrist::CastlingKeys[position.castling_rights];
    for (int square = 0; square < 64; ++square) {
        const Piece piece = position.board.squares[square];
        if (piece != Empty) key ^= zobrist::PieceKeys[piece][square];
    }
    if (position.side_to_move == 1) key ^= zobrist::SideKey;
    if (position.en_passant != NoEnPassant) {
        key ^= zobrist::EnPassantKeys[position.en_passant % 8];
    }
    return key;
}

inline int square_from_string(const std::string& text) {
    if (text.size() != 2 || text[0] < 'a' || text[0] > 'h'
        || text[1] < '1' || text[1] > '8') {
        throw std::invalid_argument("Invalid square");
    }
    return (text[1] - '1') * 8 + (text[0] - 'a');
}

inline std::string square_to_string(int square) {
    if (square == NoEnPassant) return "-";
    if (square < 0 || square >= 64) throw std::invalid_argument("Invalid square");
    std::string result = "a1";
    result[0] += square % 8;
    result[1] += square / 8;
    return result;
}

inline void load_fen(Position& position, const std::string& fen) {
    std::istringstream input(fen);
    std::string board_field, side, castling, ep, extra;
    int halfmove = 0;
    int fullmove = 0;
    if (!(input >> board_field >> side >> castling >> ep >> halfmove >> fullmove)
        || (input >> extra)) {
        throw std::invalid_argument("FEN must contain six fields");
    }
    if (halfmove < 0 || fullmove < 1) throw std::invalid_argument("Invalid move clocks");
    position.clear();

    int rank = 7;
    int file = 0;
    for (char value : board_field) {
        if (value == '/') {
            if (file != 8 || rank == 0) throw std::invalid_argument("Invalid FEN rank");
            --rank;
            file = 0;
        } else if (std::isdigit(static_cast<unsigned char>(value))) {
            const int empty = value - '0';
            if (empty < 1 || empty > 8 || file + empty > 8) {
                throw std::invalid_argument("Invalid FEN empty count");
            }
            file += empty;
        } else {
            if (file >= 8) throw std::invalid_argument("Too many FEN squares");
            position.add_piece(rank * 8 + file, piece_from_char(value));
            ++file;
        }
    }
    if (rank != 0 || file != 8) throw std::invalid_argument("Incomplete FEN board");

    if (side == "w") position.side_to_move = 0;
    else if (side == "b") position.side_to_move = 1;
    else throw std::invalid_argument("Invalid side to move");

    position.castling_rights = 0;
    if (castling != "-") {
        for (char value : castling) {
            if (value == 'K') position.castling_rights |= WhiteKingside;
            else if (value == 'Q') position.castling_rights |= WhiteQueenside;
            else if (value == 'k') position.castling_rights |= BlackKingside;
            else if (value == 'q') position.castling_rights |= BlackQueenside;
            else throw std::invalid_argument("Invalid castling rights");
        }
    }
    position.en_passant = ep == "-" ? NoEnPassant : square_from_string(ep);
    position.halfmove_clock = halfmove;
    position.fullmove_number = fullmove;
    position.hash_key = compute_hash(position);
}

inline std::string to_fen(const Position& position) {
    std::string board;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const Piece piece = position.board.squares[rank * 8 + file];
            if (piece == Empty) {
                ++empty;
            } else {
                if (empty) board += static_cast<char>('0' + empty);
                empty = 0;
                board += piece_to_char(piece);
            }
        }
        if (empty) board += static_cast<char>('0' + empty);
        if (rank) board += '/';
    }
    std::string castling;
    if (position.castling_rights & WhiteKingside) castling += 'K';
    if (position.castling_rights & WhiteQueenside) castling += 'Q';
    if (position.castling_rights & BlackKingside) castling += 'k';
    if (position.castling_rights & BlackQueenside) castling += 'q';
    if (castling.empty()) castling = "-";
    return board + " " + (position.side_to_move == 0 ? "w" : "b") + " "
        + castling + " " + square_to_string(position.en_passant) + " "
        + std::to_string(position.halfmove_clock) + " "
        + std::to_string(position.fullmove_number);
}

}  // namespace ace
