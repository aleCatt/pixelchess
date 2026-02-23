import pygame
from constants import FONT_CHAR_WIDTH, FONT_CHAR_HEIGHT, FONT_SCALE, FONT_COLS


class PixelFont:
    def __init__(self, sheet: pygame.Surface | None):
        self.sheet = sheet
        self.char_w = FONT_CHAR_WIDTH * FONT_SCALE
        self.char_h = FONT_CHAR_HEIGHT * FONT_SCALE
        self._first_char = 0x20

    def render(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        if self.sheet is None:
            return
        sheet = self._tinted(color)
        cx = x
        for char in text:
            code = ord(char) - self._first_char
            if code < 0:
                continue
            src = pygame.Rect(
                (code % FONT_COLS) * self.char_w,
                (code // FONT_COLS) * self.char_h,
                self.char_w,
                self.char_h,
            )
            surface.blit(sheet, (cx, y), src)
            cx += self.char_w

    def text_width(self, text: str) -> int:
        return len(text) * self.char_w

    def _tinted(self, color: tuple) -> pygame.Surface:
        if color == (255, 255, 255):
            return self.sheet
        tinted = self.sheet.copy()
        tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        return tinted
