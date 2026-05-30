"""radar.py — Bottom-screen radar showing all entities, including invisible ones."""
import pygame
import math
from src.constants import *


class Radar:
    def __init__(self):
        self._surf = None

    def draw(self, screen: pygame.Surface, players: list, enemies: list, dungeon: int,
             double_score: bool = False):
        rx = PLAY_X
        ry = RADAR_Y
        rw = COLS * CELL
        rh = RADAR_H

        # Background
        pygame.draw.rect(screen, RADAR_BG, (rx, ry, rw, rh))
        pygame.draw.rect(screen, (20, 40, 80), (rx, ry, rw, rh), 2)

        # Grid lines
        for c in range(0, rw, rw // 11):
            pygame.draw.line(screen, RADAR_GRID, (rx + c, ry), (rx + c, ry + rh), 1)
        pygame.draw.line(screen, RADAR_GRID, (rx, ry + rh // 2), (rx + rw, ry + rh // 2), 1)

        # Warp tunnel markers
        wr = maze_warp_row_frac = (ROWS - 1 - 4) / ROWS
        ty = int(ry + wr * rh)
        pygame.draw.line(screen, (0, 140, 120), (rx, ty), (rx + 16, ty), 2)
        pygame.draw.line(screen, (0, 140, 120), (rx + rw - 16, ty), (rx + rw, ty), 2)

        # Dot size for each entity type
        def dot(x_frac, y_frac, color, size=4, blink=False):
            if blink and int(pygame.time.get_ticks() / 120) % 2:
                return
            px = int(rx + x_frac * rw)
            py = int(ry + y_frac * rh)
            pygame.draw.circle(screen, color, (px, py), size)
            # Glow ring
            glow = tuple(min(255, v + 80) for v in color[:3])
            pygame.draw.circle(screen, glow, (px, py), size + 2, 1)

        # Draw enemies (ALL, even invisible — radar is omniscient)
        for e in enemies:
            if not e.alive:
                continue
            fx, fy = e.get_radar_pos()
            colors = {
                "burwor":  BURWOR_C,
                "garwor":  GARWOR_C,
                "thorwor": THORWOR_C,
                "worluk":  WORLUK_C,
                "wizard":  WIZARD_C,
            }
            c = colors.get(e.etype, WHITE)
            blink = e.invisible  # blink for invisible enemies
            dot(fx, fy, c, size=4, blink=blink)

        # Draw players
        for p in players:
            if p.alive:
                fx, fy = p.get_radar_pos()
                dot(fx, fy, p.color, size=5)

        # Label
        font = pygame.font.SysFont("monospace", 11, bold=True)
        lbl = font.render(f"RADAR  DUNGEON {dungeon}", True, (80, 120, 220))
        screen.blit(lbl, (rx + 8, ry + 4))

        if double_score:
            ds = font.render("★ DOUBLE SCORE ★", True, (255, 220, 50))
            screen.blit(ds, (rx + rw - ds.get_width() - 8, ry + 4))

        # Enemy count
        alive_count = sum(1 for e in enemies if e.alive)
        ct = font.render(f"ENEMIES: {alive_count}", True, (200, 80, 80))
        screen.blit(ct, (rx + rw // 2 - ct.get_width() // 2, ry + 4))
