from .pieces import Pawn, Rook, Knight, Bishop, Queen, King

WHITE = "white"
BLACK = "black"

_BACK_RANK = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
_PROMOTION_PIECES = {"queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight}


class ChessEngine:
    def __init__(self):
        self.board: list[list] = []
        self.turn: str = WHITE
        self.castling_rights: dict = {}
        self.en_passant_target: tuple[int, int] | None = None
        self.promotion_pending: tuple[int, int] | None = None
        self.move_log: list[dict] = []
        self.reset()

    def reset(self):
        self.board = self._build_starting_board()
        self.turn = WHITE
        self.en_passant_target = None
        self.promotion_pending = None
        self.move_log = []
        self.castling_rights = {
            WHITE: {"kingside": True, "queenside": True},
            BLACK: {"kingside": True, "queenside": True},
        }

    def _build_starting_board(self) -> list[list]:
        board = [[None] * 8 for _ in range(8)]
        for col, cls in enumerate(_BACK_RANK):
            board[0][col] = cls(BLACK)
            board[7][col] = cls(WHITE)
        for col in range(8):
            board[1][col] = Pawn(BLACK)
            board[6][col] = Pawn(WHITE)
        return board

    def get_piece(self, row: int, col: int):
        return self.board[row][col]

    def get_legal_moves(self, row: int, col: int) -> list[tuple[int, int]]:
        piece = self.board[row][col]
        if piece is None or piece.color != self.turn:
            return []
        return [m for m in piece.get_moves(self, row, col) if not self._causes_check(row, col, m)]

    def move_piece(self, start: tuple[int, int], end: tuple[int, int]) -> dict:
        sr, sc = start
        er, ec = end
        piece = self.board[sr][sc]

        self.move_log.append(self._log_entry(start, end, piece))
        self._apply_move(start, end, piece)
        self._update_castling_rights(piece, start)
        self._update_en_passant(piece, start, end)
        self.turn = BLACK if self.turn == WHITE else WHITE

        if isinstance(piece, Pawn) and er == (0 if piece.color == WHITE else 7):
            self.promotion_pending = (er, ec)
            return {"promotion_required": True, "promotion_square": (er, ec)}

        return {"promotion_required": False, "promotion_square": None}

    def promote_pawn(self, row: int, col: int, piece_type: str) -> None:
        cls = _PROMOTION_PIECES.get(piece_type.lower())
        if cls is None:
            raise ValueError(f"Invalid promotion piece: '{piece_type}'")
        color = self.board[row][col].color
        self.board[row][col] = cls(color)
        self.promotion_pending = None

    def is_in_check(self, color: str) -> bool:
        king_sq = self._find_king(color)
        opponent = BLACK if color == WHITE else WHITE
        return any(
            king_sq in self.board[r][c].get_moves(self, r, c)
            for r in range(8)
            for c in range(8)
            if self.board[r][c] is not None and self.board[r][c].color == opponent
        )

    def is_checkmate(self, color: str) -> bool:
        return self.is_in_check(color) and not self._has_any_legal_move(color)

    def is_stalemate(self, color: str) -> bool:
        return not self.is_in_check(color) and not self._has_any_legal_move(color)

    def find_king_square(self, color: str) -> tuple[int, int] | None:
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if isinstance(p, King) and p.color == color:
                    return (r, c)
        return None

    # -------------------------------------------------------------------------

    def _find_king(self, color: str) -> tuple[int, int]:
        sq = self.find_king_square(color)
        if sq is None:
            raise RuntimeError(f"No {color} king on board")
        return sq

    def _apply_move(self, start: tuple, end: tuple, piece) -> None:
        sr, sc = start
        er, ec = end

        if isinstance(piece, Pawn) and end == self.en_passant_target:
            self.board[sr][ec] = None

        if isinstance(piece, King):
            dc = ec - sc
            if dc == 2:
                self.board[sr][5] = self.board[sr][7]
                self.board[sr][7] = None
            elif dc == -2:
                self.board[sr][3] = self.board[sr][0]
                self.board[sr][0] = None

        self.board[er][ec] = piece
        self.board[sr][sc] = None

    def _update_castling_rights(self, piece, start: tuple) -> None:
        sr, sc = start
        if isinstance(piece, King):
            self.castling_rights[piece.color]["kingside"] = False
            self.castling_rights[piece.color]["queenside"] = False
        elif isinstance(piece, Rook):
            rights = self.castling_rights.get(piece.color, {})
            if sc == 7:
                rights["kingside"] = False
            elif sc == 0:
                rights["queenside"] = False

    def _update_en_passant(self, piece, start: tuple, end: tuple) -> None:
        sr, _ = start
        er, ec = end
        if isinstance(piece, Pawn) and abs(er - sr) == 2:
            self.en_passant_target = ((sr + er) // 2, ec)
        else:
            self.en_passant_target = None

    def _causes_check(self, fr: int, fc: int, end: tuple[int, int]) -> bool:
        er, ec = end
        moving = self.board[fr][fc]
        captured = self.board[er][ec]
        ep_sq = ep_piece = None

        if isinstance(moving, Pawn) and end == self.en_passant_target:
            ep_sq = (fr, ec)
            ep_piece = self.board[fr][ec]
            self.board[fr][ec] = None

        self.board[er][ec] = moving
        self.board[fr][fc] = None
        in_check = self.is_in_check(moving.color)
        self.board[fr][fc] = moving
        self.board[er][ec] = captured

        if ep_sq is not None:
            self.board[ep_sq[0]][ep_sq[1]] = ep_piece

        return in_check

    def _has_any_legal_move(self, color: str) -> bool:
        saved = self.turn
        self.turn = color
        result = any(
            self.get_legal_moves(r, c)
            for r in range(8)
            for c in range(8)
            if self.board[r][c] is not None and self.board[r][c].color == color
        )
        self.turn = saved
        return result

    def _log_entry(self, start: tuple, end: tuple, piece) -> dict:
        er, ec = end
        return {
            "piece": piece,
            "start": start,
            "end": end,
            "captured": self.board[er][ec],
            "en_passant_before": self.en_passant_target,
            "castling_rights_before": {
                WHITE: dict(self.castling_rights[WHITE]),
                BLACK: dict(self.castling_rights[BLACK]),
            },
        }
