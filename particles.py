import math
import random
import time

import pygame

from constants import (
    PARTICLE_COUNT, PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX,
    PARTICLE_LIFETIME, PARTICLE_SIZE, TILE_W, TILE_H,
)

_PALETTES = {
    "white": [(0xFF, 0xFF, 0xEE), (0xDD, 0xCC, 0xAA), (0xFF, 0xF0, 0x80), (0xCC, 0xBB, 0x99)],
    "black": [(0x44, 0x22, 0x11), (0x88, 0x44, 0x22), (0xCC, 0x66, 0x22), (0xFF, 0x88, 0x00)],
}


class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.born = time.monotonic()
        self.alpha = 255

    @property
    def alive(self) -> bool:
        return (time.monotonic() - self.born) < PARTICLE_LIFETIME

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 420 * dt
        age = time.monotonic() - self.born
        self.alpha = int(255 * (1.0 - age / PARTICLE_LIFETIME))

    def draw(self, surface: pygame.Surface) -> None:
        r, g, b = self.color
        surf = pygame.Surface((PARTICLE_SIZE, PARTICLE_SIZE), pygame.SRCALPHA)
        surf.fill((r, g, b, max(0, self.alpha)))
        surface.blit(surf, (int(self.x), int(self.y)))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def spawn_capture(self, tile_px: tuple[int, int], captured_color: str) -> None:
        cx = tile_px[0] + TILE_W // 2
        cy = tile_px[1] + TILE_H // 2
        palette = _PALETTES.get(captured_color, _PALETTES["white"])

        for _ in range(PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_SPEED_MIN * TILE_W, PARTICLE_SPEED_MAX * TILE_W)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - TILE_H * 1.5
            ox = random.randint(-TILE_W // 4, TILE_W // 4)
            oy = random.randint(-TILE_H // 4, TILE_H // 4)
            self.particles.append(Particle(cx + ox, cy + oy, vx, vy, random.choice(palette)))

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            p.draw(surface)
