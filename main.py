import sys
import pygame

from chess.engine import ChessEngine
from assets import AssetManager
from gui import ChessGUI
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, TARGET_FPS


def main() -> None:
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chess")

    engine = ChessEngine()
    assets = AssetManager()
    gui = ChessGUI(engine, assets)

    assets.play("game-start")
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            gui.handle_event(event)

        gui.render()
        clock.tick(TARGET_FPS)


if __name__ == "__main__":
    main()
