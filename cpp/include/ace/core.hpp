#pragma once

#include <array>
#include <cassert>
#include <cstdint>

namespace ace {

using Bitboard = std::uint64_t;
using Move = std::uint32_t;

enum Piece : std::uint8_t {
    Empty = 0,
    WhitePawn, WhiteKnight, WhiteBishop, WhiteRook, WhiteQueen, WhiteKing,
    BlackPawn, BlackKnight, BlackBishop, BlackRook, BlackQueen, BlackKing,
};

constexpr Move encode_move(
    int from, int to, Piece moving, Piece captured = Empty,
    Piece promotion = Empty, std::uint8_t flags = 0
) {
    return static_cast<Move>(from)
        | (static_cast<Move>(to) << 6)
        | (static_cast<Move>(moving) << 12)
        | (static_cast<Move>(captured) << 16)
        | (static_cast<Move>(promotion) << 20)
        | (static_cast<Move>(flags) << 24);
}

constexpr int from_square(Move move) { return move & 0x3f; }
constexpr int to_square(Move move) { return (move >> 6) & 0x3f; }
constexpr Piece moving_piece(Move move) { return static_cast<Piece>((move >> 12) & 0xf); }
constexpr Piece captured_piece(Move move) { return static_cast<Piece>((move >> 16) & 0xf); }
constexpr Piece promotion_piece(Move move) { return static_cast<Piece>((move >> 20) & 0xf); }
constexpr std::uint8_t move_flags(Move move) { return (move >> 24) & 0xff; }

class Board {
public:
    std::array<Piece, 64> squares{};
    std::array<Bitboard, 13> pieces{};
    Bitboard white = 0;
    Bitboard black = 0;
    Bitboard occupied = 0;

    void add(int square, Piece piece) {
        assert(piece != Empty && squares[square] == Empty);
        const Bitboard mask = Bitboard{1} << square;
        squares[square] = piece;
        pieces[piece] |= mask;
        (piece <= WhiteKing ? white : black) |= mask;
        occupied |= mask;
    }

    Piece remove(int square) {
        const Piece piece = squares[square];
        if (piece == Empty) return Empty;
        const Bitboard mask = Bitboard{1} << square;
        squares[square] = Empty;
        pieces[piece] &= ~mask;
        (piece <= WhiteKing ? white : black) &= ~mask;
        occupied &= ~mask;
        return piece;
    }

    void move(int from, int to) {
        const Piece piece = remove(from);
        assert(piece != Empty && squares[to] == Empty);
        add(to, piece);
    }

    bool valid() const {
        Bitboard rebuilt_white = 0;
        Bitboard rebuilt_black = 0;
        for (int piece = WhitePawn; piece <= WhiteKing; ++piece) rebuilt_white |= pieces[piece];
        for (int piece = BlackPawn; piece <= BlackKing; ++piece) rebuilt_black |= pieces[piece];
        return rebuilt_white == white && rebuilt_black == black
            && (white | black) == occupied && (white & black) == 0;
    }
};

static_assert(sizeof(Move) == 4);
static_assert(sizeof(Bitboard) == 8);

}  // namespace ace
