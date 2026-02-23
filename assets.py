import pygame
from constants import (
    ASSET_PIECE_DIR, ASSET_AUDIO_DIR, ASSET_FONT_PATH,
    PIECE_NAMES, PIECE_WIDTH, PIECE_HEIGHT, FONT_SCALE,
)

_SOUND_NAMES = ["move", "capture", "check", "castle", "promote", "illegal", "game-start", "game-end"]


class AssetManager:
    def __init__(self):
        self.pieces: dict[str, pygame.Surface] = {}
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.font_sheet: pygame.Surface | None = None
        self._load_pieces()
        self._load_audio()
        self._load_font()

    def _load_pieces(self) -> None:
        for color in ("white", "black"):
            for cls, name in PIECE_NAMES.items():
                key = f"{color}_{name}"
                path = f"{ASSET_PIECE_DIR}/{key}.png"
                try:
                    raw = pygame.image.load(path).convert_alpha()
                    self.pieces[key] = pygame.transform.scale(raw, (PIECE_WIDTH, PIECE_HEIGHT))
                except FileNotFoundError:
                    surf = pygame.Surface((PIECE_WIDTH, PIECE_HEIGHT), pygame.SRCALPHA)
                    surf.fill((255, 0, 255, 200))
                    self.pieces[key] = surf

    def _load_audio(self) -> None:
        for name in _SOUND_NAMES:
            try:
                self.sounds[name] = pygame.mixer.Sound(f"{ASSET_AUDIO_DIR}/{name}.mp3")
            except FileNotFoundError:
                pass

    def _load_font(self) -> None:
        try:
            raw = pygame.image.load(ASSET_FONT_PATH).convert_alpha()
            w, h = raw.get_width() * FONT_SCALE, raw.get_height() * FONT_SCALE
            self.font_sheet = pygame.transform.scale(raw, (w, h))
        except FileNotFoundError:
            self.font_sheet = None

    def get_piece_sprite(self, piece) -> pygame.Surface:
        return self.pieces[f"{piece.color}_{PIECE_NAMES[type(piece)]}"]

    def play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound:
            sound.play()
