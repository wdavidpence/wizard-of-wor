"""bullet.py — Laser bolts (player and enemy)."""
import pygame
from src.constants import *


class Bullet:
    DIRS = {
        "right": (1, 0),
        "left":  (-1, 0),
        "up":    (0, -1),
        "down":  (0,  1),
    }

    def __init__(self, col: float, row: float, direction: str,
                 color: tuple, owner: str = "enemy", damage: int = 1):
        self.col   = col
        self.row   = row
        self.dir   = direction
        self.dc, self.dr = self.DIRS[direction]
        self.color = color
        self.owner = owner   # "p1", "p2", "enemy"
        self.damage = damage
        self.alive = True
        self.speed = BULLET_SPEED   # cells/sec
        self._trail: list = []

    def update(self, dt: float, maze, particles=None):
        self.col += self.dc * self.speed * dt
        self.row += self.dr * self.speed * dt

        ic, ir = int(self.col + 0.5), int(self.row + 0.5)

        # Hit wall — spawn explosion particles!
        if maze.is_wall(ic, ir):
            self.alive = False
            # ── CRITICAL FIX #2: Explode on wall hit ──
            if particles is not None:
                px = PLAY_X + ic * CELL
                py = PLAY_Y + ir * CELL
                # Offset slightly towards direction of travel
                if self.dc > 0:   px += CELL - 8
                elif self.dc < 0: px += 8
                if self.dr > 0:   py += CELL - 8
                elif self.dr < 0: py += 8
                particles.explode(int(px), int(py), WALL, 8)
            return

        # Wrap through warp tunnels
        wt = maze.is_warp(ic, ir)
        if wt:
            if wt == WARP_L:
                self.col = COLS - 2.0
            else:
                self.col = 1.0

        # Trail for visual effect
        px = PLAY_X + self.col * CELL
        py = PLAY_Y + self.row * CELL
        self._trail.append((px, py))
        if len(self._trail) > 6:
            self._trail.pop(0)

    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return
        cx = int(PLAY_X + self.col * CELL)
        cy = int(PLAY_Y + self.row * CELL)

        # Draw trail
        for i, (tx, ty) in enumerate(self._trail):
            alpha = int(60 * (i / max(len(self._trail), 1)))
            r, g, b = self.color
            trail_col = (r, g, b)
            pygame.draw.circle(screen, trail_col, (int(tx), int(ty)), 2)

        # Draw bolt
        if self.dc != 0:  # horizontal
            rect = pygame.Rect(cx - 12, cy - 4, 24, 8)
        else:
            rect = pygame.Rect(cx - 4, cy - 12, 8, 24)

        pygame.draw.rect(screen, self.color, rect, border_radius=4)
        # Bright core
        core_color = tuple(min(255, v + 80) for v in self.color)
        if self.dc != 0:
            pygame.draw.rect(screen, core_color, rect.inflate(-8, -4), border_radius=2)
        else:
            pygame.draw.rect(screen, core_color, rect.inflate(-4, -8), border_radius=2)

    def get_rect(self) -> pygame.Rect:
        cx = int(PLAY_X + self.col * CELL)
        cy = int(PLAY_Y + self.row * CELL)
        # 28×28 rect to match enemy hitboxes and ensure AABB overlap
        # at cell-boundary positions (was 20×20, causing gap at edges)
        return pygame.Rect(cx - 14, cy - 14, 28, 28)
