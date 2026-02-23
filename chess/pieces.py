from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import ChessEngine


class Piece:
    def __init__(self, color: str):
        self.color = color

    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        raise NotImplementedError

    def is_enemy(self, engine: ChessEngine, row: int, col: int) -> bool:
        piece = engine.board[row][col]
        return piece is not None and piece.color != self.color

    def is_friendly(self, engine: ChessEngine, row: int, col: int) -> bool:
        piece = engine.board[row][col]
        return piece is not None and piece.color == self.color

    def is_empty(self, engine: ChessEngine, row: int, col: int) -> bool:
        return engine.board[row][col] is None

    @staticmethod
    def in_bounds(row: int, col: int) -> bool:
        return 0 <= row <= 7 and 0 <= col <= 7

    def slide(
        self,
        engine: ChessEngine,
        row: int,
        col: int,
        directions: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        moves = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while self.in_bounds(r, c):
                if self.is_empty(engine, r, c):
                    moves.append((r, c))
                elif self.is_enemy(engine, r, c):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves


class Pawn(Piece):
    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        moves = []
        direction = -1 if self.color == "white" else 1
        start_row = 6 if self.color == "white" else 1

        one_ahead = (row + direction, col)
        if self.in_bounds(*one_ahead) and self.is_empty(engine, *one_ahead):
            moves.append(one_ahead)
            two_ahead = (row + 2 * direction, col)
            if row == start_row and self.is_empty(engine, *two_ahead):
                moves.append(two_ahead)

        for dc in (-1, 1):
            target = (row + direction, col + dc)
            if not self.in_bounds(*target):
                continue
            if self.is_enemy(engine, *target) or target == engine.en_passant_target:
                moves.append(target)

        return moves


class Rook(Piece):
    DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        return self.slide(engine, row, col, self.DIRECTIONS)


class Knight(Piece):
    JUMPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        return [
            (row + dr, col + dc)
            for dr, dc in self.JUMPS
            if self.in_bounds(row + dr, col + dc)
            and not self.is_friendly(engine, row + dr, col + dc)
        ]


class Bishop(Piece):
    DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        return self.slide(engine, row, col, self.DIRECTIONS)


class Queen(Piece):
    DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        return self.slide(engine, row, col, self.DIRECTIONS)


class King(Piece):
    STEPS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def get_moves(self, engine: ChessEngine, row: int, col: int) -> list[tuple[int, int]]:
        moves = [
            (row + dr, col + dc)
            for dr, dc in self.STEPS
            if self.in_bounds(row + dr, col + dc)
            and not self.is_friendly(engine, row + dr, col + dc)
        ]

        rights = engine.castling_rights.get(self.color, {})
        if rights.get("kingside") and self._kingside_clear(engine, row):
            moves.append((row, col + 2))
        if rights.get("queenside") and self._queenside_clear(engine, row):
            moves.append((row, col - 2))

        return moves

    def _kingside_clear(self, engine: ChessEngine, row: int) -> bool:
        return self.is_empty(engine, row, 5) and self.is_empty(engine, row, 6)

    def _queenside_clear(self, engine: ChessEngine, row: int) -> bool:
        return (
            self.is_empty(engine, row, 1)
            and self.is_empty(engine, row, 2)
            and self.is_empty(engine, row, 3)
        )
