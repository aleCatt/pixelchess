import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess.engine import ChessEngine
from chess.pieces import King, Queen, Rook, Knight, Bishop, Pawn


@pytest.fixture
def engine():
    return ChessEngine()


def test_starting_turn_is_white(engine):
    assert engine.turn == "white"


def test_pawn_has_two_opening_moves(engine):
    moves = engine.get_legal_moves(6, 0)  # white a-pawn
    assert len(moves) == 2


def test_pawn_blocked_by_own_piece(engine):
    engine.board[5][0] = Pawn("white")
    moves = engine.get_legal_moves(6, 0)
    assert (5, 0) not in moves


def test_knight_opening_moves(engine):
    moves = engine.get_legal_moves(7, 1)  # white queenside knight
    assert len(moves) == 2


def test_no_legal_moves_for_wrong_color(engine):
    assert engine.get_legal_moves(1, 0) == []  # black pawn, white's turn


def test_not_in_check_at_start(engine):
    assert not engine.is_in_check("white")
    assert not engine.is_in_check("black")


def test_not_checkmate_or_stalemate_at_start(engine):
    assert not engine.is_checkmate("white")
    assert not engine.is_stalemate("white")


def test_move_piece_changes_turn(engine):
    engine.move_piece((6, 0), (5, 0))
    assert engine.turn == "black"


def test_en_passant_target_set_on_double_push(engine):
    engine.move_piece((6, 4), (4, 4))  # white e-pawn double push
    assert engine.en_passant_target == (5, 4)


def test_en_passant_target_cleared_on_next_move(engine):
    engine.move_piece((6, 4), (4, 4))
    engine.move_piece((1, 0), (2, 0))  # black moves
    assert engine.en_passant_target is None


def test_castling_rights_revoked_after_king_move(engine):
    # Clear squares between king and rook
    engine.board[7][5] = None
    engine.board[7][6] = None
    engine.move_piece((7, 4), (7, 6))  # kingside castle
    assert not engine.castling_rights["white"]["kingside"]
    assert not engine.castling_rights["white"]["queenside"]


def test_promotion_required_flag(engine):
    # Place white pawn one step from promotion
    engine.board[1][0] = Pawn("white")
    engine.board[0][0] = None  # clear the black rook
    result = engine.move_piece((1, 0), (0, 0))
    assert result["promotion_required"] is True
    assert result["promotion_square"] == (0, 0)


def test_promote_pawn_replaces_piece(engine):
    engine.board[0][0] = Pawn("white")
    engine.promote_pawn(0, 0, "queen")
    assert isinstance(engine.board[0][0], Queen)


def test_promote_pawn_invalid_type_raises(engine):
    engine.board[0][0] = Pawn("white")
    with pytest.raises(ValueError):
        engine.promote_pawn(0, 0, "dragon")


def test_move_into_check_is_illegal(engine):
    """A move that exposes the king to check must not appear in legal moves."""
    # Isolate: put white king in a vulnerable position by hand
    engine.board = [[None] * 8 for _ in range(8)]
    engine.board[7][4] = King("white")
    engine.board[7][3] = Rook("white")  # pinned rook
    engine.board[7][0] = Rook("black")  # attacker along rank 7
    engine.board[0][4] = King("black")

    legal = engine.get_legal_moves(7, 3)
    # The pinned rook must not move off rank 7 (that would expose the king)
    off_rank = [(r, 3) for r in range(7) if r != 7]
    for sq in off_rank:
        assert sq not in legal
