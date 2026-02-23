import math
import time

import pygame

from chess.engine import ChessEngine
from chess.pieces import King, Pawn
from assets import AssetManager
from font import PixelFont
from particles import ParticleSystem
from constants import *


def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) ** 2


class ChessGUI:
    """
    Pixel-art chess front-end.

    Coordinate conventions
    ----------------------
    Engine board: (row, col)  — row 0 = black back rank, row 7 = white back rank
    Screen pixel: (px, py)    — origin at top-left of window

    Board is rotated 90° from the standard top-down view:
      - Ranks (rows) run left → right.  Row 7 (white) is at x = BOARD_ORIGIN_X.
      - Files (cols) run top → bottom.  Col 0 (a-file) is at y = BOARD_ORIGIN_Y.
    """

    def __init__(self, engine: ChessEngine, assets: AssetManager):
        self.engine = engine
        self.assets = assets
        self.font = PixelFont(assets.font_sheet)
        self.screen = pygame.display.get_surface()
        self.particles = ParticleSystem()

        self.selected_square: tuple[int, int] | None = None
        self.legal_moves: list[tuple[int, int]] = []
        self.dragging = False
        self.drag_piece_pos: tuple[int, int] = (0, 0)
        self.drag_origin: tuple[int, int] | None = None

        self.animating = False
        self.anim_piece = None
        self.anim_origin: tuple[int, int] | None = None
        self.anim_dest: tuple[int, int] | None = None
        self.anim_start_px: tuple[int, int] = (0, 0)
        self.anim_end_px: tuple[int, int] = (0, 0)
        self.anim_start_time: float = 0.0

        self.promotion_active = False
        self.promotion_square: tuple[int, int] | None = None
        self.promotion_rects: list[pygame.Rect] = []
        self.promotion_color: str = "white"

        self.game_over = False
        self.game_over_msg: str = ""

        self._last_frame_time: float = time.monotonic()

    # -------------------------------------------------------------------------
    # Coordinate helpers
    # -------------------------------------------------------------------------

    def tile_to_pixel(self, row: int, col: int) -> tuple[int, int]:
        return (BOARD_ORIGIN_X + (7 - row) * TILE_W, BOARD_ORIGIN_Y + col * TILE_H)

    def pixel_to_tile(self, px: int, py: int) -> tuple[int, int] | None:
        bx, by = px - BOARD_ORIGIN_X, py - BOARD_ORIGIN_Y
        if not (0 <= bx < BOARD_W and 0 <= by < BOARD_H):
            return None
        return (7 - bx // TILE_W, by // TILE_H)

    def piece_pixel_pos(self, row: int, col: int) -> tuple[int, int]:
        tx, ty = self.tile_to_pixel(row, col)
        return (tx, ty + PIECE_Y_OFFSET)

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._restart()
            return

        if self.promotion_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_promotion_click(event.pos)
            return

        if self.animating:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_mouse_down(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.drag_piece_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._on_mouse_up(event.pos)

    def render(self) -> None:
        now = time.monotonic()
        dt = now - self._last_frame_time
        self._last_frame_time = now

        self.particles.update(dt)

        self.screen.fill(COLOR_BORDER)
        self._draw_board()
        self._draw_border_rank_numbers_top()
        self._draw_pieces()
        self._draw_border()
        self._draw_border_labels()
        self._draw_promotion_menu()
        self._draw_game_over()
        pygame.display.flip()

    # -------------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------------

    def _on_mouse_down(self, pos: tuple[int, int]) -> None:
        tile = self.pixel_to_tile(*pos)
        if tile is None:
            return

        row, col = tile
        piece = self.engine.get_piece(row, col)

        if piece is not None and piece.color == self.engine.turn:
            self.selected_square = tile
            self.legal_moves = self.engine.get_legal_moves(row, col)
            self.dragging = True
            self.drag_origin = tile
            self.drag_piece_pos = pos
            return

        if tile in self.legal_moves:
            self._commit_move(self.selected_square, tile)
            return

        self.selected_square = None
        self.legal_moves = []

    def _on_mouse_up(self, pos: tuple[int, int]) -> None:
        if not self.dragging:
            return
        self.dragging = False
        tile = self.pixel_to_tile(*pos)
        if tile is not None and tile in self.legal_moves:
            self._commit_move(self.drag_origin, tile)
        else:
            if tile != self.drag_origin:
                self.assets.play("illegal")
            self.drag_origin = None

    def _handle_promotion_click(self, pos: tuple[int, int]) -> None:
        for i, rect in enumerate(self.promotion_rects):
            if rect.collidepoint(pos):
                self.engine.promote_pawn(*self.promotion_square, PROMOTION_CHOICES[i])
                self.promotion_active = False
                self.promotion_square = None
                self.assets.play("promote")
                self._check_game_end()
                return

    # -------------------------------------------------------------------------
    # Move application
    # -------------------------------------------------------------------------

    def _commit_move(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        if start is None:
            return
        moving = self.engine.get_piece(*start)
        if moving is None:
            return

        sound = self._choose_sound(start, end, moving)
        captured = self._captured_piece(start, end, moving)

        self._start_animation(start, end, moving)
        if captured is not None:
            self.particles.spawn_capture(self.tile_to_pixel(*end), captured.color)

        result = self.engine.move_piece(start, end)
        self.assets.play(sound)

        if result["promotion_required"]:
            self._begin_promotion(result["promotion_square"], moving.color)
            return

        self._check_game_end()
        self.selected_square = None
        self.legal_moves = []
        self.drag_origin = None

    def _choose_sound(self, start: tuple, end: tuple, piece) -> str:
        er, ec = end
        target = self.engine.get_piece(er, ec)
        if isinstance(piece, King) and abs(ec - start[1]) == 2:
            return "castle"
        if (target is not None and target.color != piece.color) or (
            isinstance(piece, Pawn) and end == self.engine.en_passant_target
        ):
            return "capture"
        return "move"

    def _captured_piece(self, start: tuple, end: tuple, moving):
        er, ec = end
        target = self.engine.get_piece(er, ec)
        if target is not None and target.color != moving.color:
            return target
        if isinstance(moving, Pawn) and end == self.engine.en_passant_target:
            return self.engine.get_piece(start[0], ec)
        return None

    def _check_game_end(self) -> None:
        current = self.engine.turn
        if self.engine.is_checkmate(current):
            winner = "BLACK" if current == "white" else "WHITE"
            self.game_over = True
            self.game_over_msg = f"{winner} WINS BY CHECKMATE"
            self.assets.play("game-end")
        elif self.engine.is_stalemate(current):
            self.game_over = True
            self.game_over_msg = "DRAW BY STALEMATE"
            self.assets.play("game-end")
        elif self.engine.is_in_check(current):
            self.assets.play("check")

    def _restart(self) -> None:
        self.engine.reset()
        self.selected_square = None
        self.legal_moves = []
        self.dragging = False
        self.drag_origin = None
        self.animating = False
        self.anim_origin = None
        self.anim_dest = None
        self.promotion_active = False
        self.promotion_square = None
        self.game_over = False
        self.game_over_msg = ""
        self.particles = ParticleSystem()
        self.assets.play("game-start")

    def _begin_promotion(self, square: tuple[int, int], color: str) -> None:
        self.promotion_active = True
        self.promotion_square = square
        self.promotion_color = color
        self.selected_square = None
        self.legal_moves = []
        self.drag_origin = None

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    def _start_animation(self, start: tuple, end: tuple, piece) -> None:
        self.animating = True
        self.anim_piece = piece
        self.anim_origin = start
        self.anim_dest = end
        self.anim_start_px = self.piece_pixel_pos(*start)
        self.anim_end_px = self.piece_pixel_pos(*end)
        self.anim_start_time = time.monotonic()

    def _draw_animated_piece(self) -> None:
        elapsed = time.monotonic() - self.anim_start_time
        t = _ease_out(min(elapsed / ANIMATION_DURATION, 1.0))
        sx, sy = self.anim_start_px
        ex, ey = self.anim_end_px
        self.screen.blit(
            self.assets.get_piece_sprite(self.anim_piece),
            (int(sx + (ex - sx) * t), int(sy + (ey - sy) * t)),
        )
        if elapsed >= ANIMATION_DURATION:
            self.animating = False
            self.anim_origin = None
            self.anim_dest = None

    # -------------------------------------------------------------------------
    # Board drawing
    # -------------------------------------------------------------------------

    def _draw_board(self) -> None:
        checked_king = self._checked_king_square()
        for row in range(8):
            for col in range(8):
                self._draw_tile(row, col, checked_king)

    def _draw_tile(self, row: int, col: int, checked_king: tuple | None) -> None:
        tx, ty = self.tile_to_pixel(row, col)
        sq = (row, col)
        base = COLOR_LIGHT_SQUARE if (row + col) % 2 == 0 else COLOR_DARK_SQUARE
        pygame.draw.rect(self.screen, base, (tx, ty, TILE_W, TILE_H))

        if sq == self.selected_square:
            self._overlay_tile(tx, ty, COLOR_HIGHLIGHT, ALPHA_HIGHLIGHT)

        if sq == checked_king:
            self._overlay_tile(tx, ty, COLOR_CHECK_SQUARE, ALPHA_CHECK)
            return

        if sq in self.legal_moves:
            target = self.engine.get_piece(row, col)
            is_capture = target is not None and target.color != self.engine.turn
            color = COLOR_LEGAL_CAPTURE if is_capture else COLOR_LEGAL_MOVE
            alpha = ALPHA_LEGAL_CAPTURE if is_capture else ALPHA_LEGAL_MOVE
            self._overlay_tile(tx, ty, color, alpha // 2)
            border = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
            pygame.draw.rect(border, (*color, alpha), (0, 0, TILE_W, TILE_H), UNIT)
            self.screen.blit(border, (tx, ty))

    def _overlay_tile(self, tx: int, ty: int, color: tuple, alpha: int) -> None:
        surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
        surf.fill((*color, alpha))
        self.screen.blit(surf, (tx, ty))

    def _checked_king_square(self) -> tuple[int, int] | None:
        for color in ("white", "black"):
            if self.engine.is_in_check(color):
                return self.engine.find_king_square(color)
        return None

    # -------------------------------------------------------------------------
    # Piece drawing
    # -------------------------------------------------------------------------

    def _draw_pieces(self) -> None:
        skip = set()
        if self.animating:
            skip.add(self.anim_origin)
            skip.add(self.anim_dest)
        if self.dragging:
            skip.add(self.drag_origin)

        for col in range(8):
            for row in range(8):
                if (row, col) in skip:
                    continue
                piece = self.engine.get_piece(row, col)
                if piece is None:
                    continue
                px, py = self.piece_pixel_pos(row, col)
                dx, dy = self._tremor_offset(row, col)
                self.screen.blit(self.assets.get_piece_sprite(piece), (px + dx, py + dy))

        if self.animating:
            self._draw_animated_piece()

        self.particles.draw(self.screen)

        if self.dragging and self.drag_origin is not None:
            piece = self.engine.get_piece(*self.drag_origin)
            if piece is not None:
                sprite = self.assets.get_piece_sprite(piece).copy()
                sprite.set_alpha(ALPHA_DRAG_PIECE)
                self.screen.blit(
                    sprite,
                    (self.drag_piece_pos[0] - PIECE_WIDTH // 2,
                     self.drag_piece_pos[1] - PIECE_HEIGHT // 2),
                )

    def _tremor_offset(self, row: int, col: int) -> tuple[int, int]:
        piece = self.engine.get_piece(row, col)
        if not isinstance(piece, King) or not self.engine.is_in_check(piece.color):
            return (0, 0)
        t = time.monotonic()
        dx = int(math.sin(t * TREMOR_FREQUENCY * 2 * math.pi) * TREMOR_AMPLITUDE)
        dy = int(math.cos(t * TREMOR_FREQUENCY * 2 * math.pi * 0.7) * TREMOR_AMPLITUDE)
        return (dx, dy)

    # -------------------------------------------------------------------------
    # Border / labels
    # -------------------------------------------------------------------------

    def _draw_border(self) -> None:
        line_y = BOARD_ORIGIN_Y + BOARD_H
        pygame.draw.rect(self.screen, (0x30, 0x20, 0x10), (BOARD_ORIGIN_X, line_y, BOARD_W, UNIT // 2))

        turn_text = f"{self.engine.turn.upper()} TO MOVE"
        tw = self.font.text_width(turn_text)
        label_y = line_y + BORDER_BOTTOM - FONT_CHAR_HEIGHT * FONT_SCALE - UNIT * 2
        label_x = BOARD_ORIGIN_X + BOARD_W - tw - UNIT * 2
        self.font.render(self.screen, turn_text, label_x, label_y)

    def _draw_border_rank_numbers_top(self) -> None:
        cw, ch = self.font.char_w, self.font.char_h
        cy = (BORDER_TOP - ch) // 2
        for r in range(8):
            label = str(8 - r)
            cx = BOARD_ORIGIN_X + (7 - r) * TILE_W + (TILE_W - cw) // 2
            self.font.render(self.screen, label, cx, cy, COLOR_LABEL)

    def _draw_border_labels(self) -> None:
        cw, ch = self.font.char_w, self.font.char_h

        for c in range(8):
            letter = chr(ord('a') + c)
            cy = BOARD_ORIGIN_Y + c * TILE_H + (TILE_H - ch) // 2
            self.font.render(self.screen, letter, (BORDER_SIDE - cw) // 2, cy, COLOR_LABEL)
            cx_right = BOARD_ORIGIN_X + BOARD_W + (BORDER_SIDE - cw) // 2
            self.font.render(self.screen, letter, cx_right, cy, COLOR_LABEL)

        cy_bot = BOARD_ORIGIN_Y + BOARD_H + UNIT * 2
        for r in range(8):
            label = str(8 - r)
            cx = BOARD_ORIGIN_X + (7 - r) * TILE_W + (TILE_W - cw) // 2
            self.font.render(self.screen, label, cx, cy_bot, COLOR_LABEL)

    # -------------------------------------------------------------------------
    # Overlays
    # -------------------------------------------------------------------------

    def _draw_promotion_menu(self) -> None:
        if not self.promotion_active:
            return

        n = len(PROMOTION_CHOICES)
        panel_w = n * TILE_W + 4 * UNIT
        panel_h = PIECE_HEIGHT + 4 * UNIT
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2

        dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        pygame.draw.rect(self.screen, COLOR_PROMO_BG, (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, COLOR_PROMO_BORDER, (panel_x, panel_y, panel_w, panel_h), 2 * UNIT)

        self.promotion_rects = []
        for i, name in enumerate(PROMOTION_CHOICES):
            sprite = self.assets.pieces.get(f"{self.promotion_color}_{name}")
            ix = panel_x + 2 * UNIT + i * TILE_W
            iy = panel_y + 2 * UNIT
            if sprite:
                self.screen.blit(sprite, (ix, iy))
            self.promotion_rects.append(pygame.Rect(ix, iy, TILE_W, PIECE_HEIGHT))

    def _draw_game_over(self) -> None:
        if not self.game_over:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*COLOR_OVERLAY_BG, ALPHA_OVERLAY))
        self.screen.blit(overlay, (0, 0))

        line_h = FONT_CHAR_HEIGHT * FONT_SCALE
        tx = (WINDOW_WIDTH - self.font.text_width(self.game_over_msg)) // 2
        ty = WINDOW_HEIGHT // 2 - line_h
        self.font.render(self.screen, self.game_over_msg, tx, ty)

        sub = "CLICK TO RESTART"
        self.font.render(
            self.screen, sub,
            (WINDOW_WIDTH - self.font.text_width(sub)) // 2,
            ty + line_h + 2 * UNIT,
            (180, 180, 180),
        )
