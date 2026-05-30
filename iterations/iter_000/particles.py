"""particles.py — Explosion and neon glow particle effects."""
import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, speed=None, size=None, life=None):
        angle = random.uniform(0, math.pi * 2)
        spd   = speed or random.uniform(40, 160)
        self.x  = float(x)
        self.y  = float(y)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.color = color
        self.size  = size or random.uniform(2, 6)
        self.life  = life or random.uniform(0.3, 0.8)
        self.max_life = self.life

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.92
        self.vy *= 0.92
        self.life -= dt
        return self.life > 0

    def draw(self, screen: pygame.Surface):
        alpha = max(0, self.life / self.max_life)
        c = tuple(int(v * alpha) for v in self.color)
        r = max(1, int(self.size * alpha))
        pygame.draw.circle(screen, c, (int(self.x), int(self.y)), r)


class ParticleSystem:
    def __init__(self):
        self._particles: list[Particle] = []

    def explode(self, x: int, y: int, color: tuple, count: int = 20,
                speed: float = None):
        for _ in range(count):
            self._particles.append(Particle(x, y, color, speed=speed))
        # Add some bright core sparks
        for _ in range(count // 4):
            bright = tuple(min(255, v + 100) for v in color)
            self._particles.append(Particle(x, y, bright, speed=(speed or 80) * 1.5,
                                             size=2, life=0.2))

    def warp_flash(self, x: int, y: int):
        for _ in range(30):
            c = (0, 200 + random.randint(0, 55), 200 + random.randint(0, 55))
            self._particles.append(Particle(x, y, c, speed=random.uniform(60, 200),
                                             size=random.uniform(2, 5)))

    def update(self, dt: float):
        self._particles = [p for p in self._particles if p.update(dt)]

    def draw(self, screen: pygame.Surface):
        for p in self._particles:
            p.draw(screen)
