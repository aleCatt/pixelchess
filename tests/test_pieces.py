import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess.engine import ChessEngine
from chess.pieces import Pawn, Rook, Knight, Bishop, Queen, King


def blank_engine():
    """Engine with an empty board and white to move."""
    e = ChessEngine()
    e.board = [[None] * 8 for _ in range(8)]
    e.castling_rights = {
        "white": {"kingside": False, "queenside": False},
        "black": {"kingside": False, "queenside": False},
    }
    return e


# ---------------------------------------------------------------------------
# Pawn
# ---------------------------------------------------------------------------

def test_pawn_single_push():
    e = blank_engine()
    e.board[4][4] = Pawn("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert (3, 4) in moves


def test_pawn_double_push_from_start():
    e = blank_engine()
    e.board[6][4] = Pawn("white")
    moves = e.board[6][4].get_moves(e, 6, 4)
    assert (4, 4) in moves


def test_pawn_double_push_blocked():
    e = blank_engine()
    e.board[6][4] = Pawn("white")
    e.board[5][4] = Pawn("black")
    moves = e.board[6][4].get_moves(e, 6, 4)
    assert (4, 4) not in moves
    assert (5, 4) not in moves


def test_pawn_diagonal_capture():
    e = blank_engine()
    e.board[4][4] = Pawn("white")
    e.board[3][5] = Pawn("black")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert (3, 5) in moves


def test_pawn_cannot_capture_friendly():
    e = blank_engine()
    e.board[4][4] = Pawn("white")
    e.board[3][5] = Pawn("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert (3, 5) not in moves


def test_pawn_en_passant():
    e = blank_engine()
    e.board[3][4] = Pawn("white")
    e.en_passant_target = (2, 5)
    moves = e.board[3][4].get_moves(e, 3, 4)
    assert (2, 5) in moves


# ---------------------------------------------------------------------------
# Rook
# ---------------------------------------------------------------------------

def test_rook_open_file():
    e = blank_engine()
    e.board[4][4] = Rook("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert len(moves) == 14  # 7 along rank + 7 along file


def test_rook_blocked_by_friendly():
    e = blank_engine()
    e.board[4][4] = Rook("white")
    e.board[4][6] = Rook("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert (4, 6) not in moves
    assert (4, 7) not in moves


def test_rook_can_capture_enemy():
    e = blank_engine()
    e.board[4][4] = Rook("white")
    e.board[4][6] = Rook("black")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert (4, 6) in moves
    assert (4, 7) not in moves


# ---------------------------------------------------------------------------
# Knight
# ---------------------------------------------------------------------------

def test_knight_center_has_eight_moves():
    e = blank_engine()
    e.board[4][4] = Knight("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert len(moves) == 8


def test_knight_corner_has_two_moves():
    e = blank_engine()
    e.board[0][0] = Knight("white")
    moves = e.board[0][0].get_moves(e, 0, 0)
    assert len(moves) == 2


def test_knight_jumps_over_pieces():
    e = blank_engine()
    e.board[4][4] = Knight("white")
    # Fill all adjacent squares — knight should still have 8 moves
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr != 0 or dc != 0:
                e.board[4 + dr][4 + dc] = Pawn("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert len(moves) == 8


# ---------------------------------------------------------------------------
# Bishop
# ---------------------------------------------------------------------------

def test_bishop_open_diagonal():
    e = blank_engine()
    e.board[4][4] = Bishop("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert len(moves) == 13


# ---------------------------------------------------------------------------
# Queen
# ---------------------------------------------------------------------------

def test_queen_open_board():
    e = blank_engine()
    e.board[4][4] = Queen("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert len(moves) == 27  # 14 rook + 13 bishop


# ---------------------------------------------------------------------------
# King
# ---------------------------------------------------------------------------

def test_king_center_moves():
    e = blank_engine()
    e.board[4][4] = King("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert len(moves) == 8


def test_king_cannot_move_to_friendly_square():
    e = blank_engine()
    e.board[4][4] = King("white")
    e.board[3][4] = Pawn("white")
    moves = e.board[4][4].get_moves(e, 4, 4)
    assert (3, 4) not in moves
