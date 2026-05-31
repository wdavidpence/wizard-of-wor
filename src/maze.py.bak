"""maze.py — Maze generation, rendering, and wall collision."""
import pygame
import random
from src.constants import *


# ── Cell types ────────────────────────────────────────────────────────────────
EMPTY    = 0
WALL     = 1
WARP_L   = 2   # left warp tunnel entrance
WARP_R   = 3   # right warp tunnel entrance


# ── Pre-defined maze templates (1=wall, 0=floor) 22×14 ───────────────────────
# Each row is cols 0-21; row 0 is top.
# Border walls are always solid — not in the template arrays.
# Templates are interior-only data: 20×12 cells (cols 1-20, rows 1-12).

def _mirror(half: list[list[int]]) -> list[list[int]]:
    """Mirror a 10-col half-template to full 20 cols."""
    return [row + row[::-1] for row in half]

# Half-templates (10 cols, 12 rows) — mirrored for symmetry
_HALVES = [
    # Template 0 — classic cross channels
    [[0,0,1,0,0,0,0,1,0,0],
     [0,0,1,0,1,0,0,1,0,0],
     [0,0,0,0,1,0,0,0,0,0],
     [1,1,0,0,0,0,0,0,1,1],
     [0,0,0,1,0,0,1,0,0,0],
     [0,1,0,1,0,0,1,0,1,0],
     [0,1,0,0,0,0,0,0,1,0],
     [0,0,0,1,0,0,1,0,0,0],
     [1,1,0,0,0,0,0,0,1,1],
     [0,0,0,0,1,0,0,0,0,0],
     [0,0,1,0,1,0,0,1,0,0],
     [0,0,1,0,0,0,0,1,0,0]],
    # Template 1 — zigzag corridors
    [[0,1,0,0,1,0,0,1,0,0],
     [0,1,0,1,1,0,1,1,0,0],
     [0,0,0,1,0,0,1,0,0,0],
     [1,0,0,1,0,0,1,0,0,1],
     [0,0,0,0,0,0,0,0,0,0],
     [0,1,1,0,1,1,0,1,1,0],
     [0,1,1,0,1,1,0,1,1,0],
     [0,0,0,0,0,0,0,0,0,0],
     [1,0,0,1,0,0,1,0,0,1],
     [0,0,0,1,0,0,1,0,0,0],
     [0,0,1,1,0,1,1,0,0,0],
     [0,0,1,0,0,0,1,0,0,0]],
    # Template 2 — open corridors
    [[0,0,0,0,0,0,0,0,0,0],
     [0,1,0,1,0,0,1,0,1,0],
     [0,1,0,1,0,0,1,0,1,0],
     [0,0,0,0,0,0,0,0,0,0],
     [1,1,0,0,1,1,0,0,1,1],
     [0,0,0,0,1,1,0,0,0,0],
     [0,0,0,0,1,1,0,0,0,0],
     [1,1,0,0,1,1,0,0,1,1],
     [0,0,0,0,0,0,0,0,0,0],
     [0,1,0,1,0,0,1,0,1,0],
     [0,1,0,1,0,0,1,0,1,0],
     [0,0,0,0,0,0,0,0,0,0]],
    # Template 3 — maze-like
    [[1,0,0,1,0,0,1,0,0,1],
     [0,0,1,0,0,1,0,0,1,0],
     [0,1,0,0,1,0,0,1,0,0],
     [0,0,0,1,0,0,1,0,0,0],
     [0,1,0,0,0,0,0,0,1,0],
     [1,0,0,0,1,1,0,0,0,1],
     [1,0,0,0,1,1,0,0,0,1],
     [0,1,0,0,0,0,0,0,1,0],
     [0,0,0,1,0,0,1,0,0,0],
     [0,1,0,0,1,0,0,1,0,0],
     [0,0,1,0,0,1,0,0,1,0],
     [1,0,0,1,0,0,1,0,0,1]],
]

_TEMPLATES = [_mirror(h) for h in _HALVES]

# Arena: mostly open center
_ARENA_INTERIOR = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0],
    [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
    [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# Pit: NO interior walls
_PIT_INTERIOR = [[0]*20 for _ in range(12)]


class Maze:
    """Manages the dungeon grid, wall collision, and rendering."""

    def __init__(self, dungeon_number: int = 1):
        self.dungeon = dungeon_number
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self._build(dungeon_number)
        self._wall_surf = None   # cached render surface
        self._dirty = True

    # ── Build ────────────────────────────────────────────────────────────────

    def _build(self, n: int):
        # Fill border walls
        for c in range(COLS):
            self.grid[0][c] = WALL
            self.grid[ROWS - 1][c] = WALL
        for r in range(ROWS):
            self.grid[r][0] = WALL
            self.grid[r][COLS - 1] = WALL

        # Pick interior template
        if n == ARENA_DUNGEON:
            interior = _ARENA_INTERIOR
        elif (n == PIT_DUNGEON) or ((n > PIT_DUNGEON) and (n - PIT_DUNGEON) % PIT_REPEAT == 0):
            interior = _PIT_INTERIOR
        else:
            pool = _TEMPLATES
            # After dungeon 7, prefer more open templates
            if n >= WORLORD_DUNGEON:
                pool = [_TEMPLATES[2], _TEMPLATES[0]]
            interior = random.choice(pool)

        # Copy interior (rows 1-12, cols 1-20)
        for r in range(12):
            for c in range(20):
                self.grid[r + 1][c + 1] = WALL if interior[r][c] else EMPTY

        # Warp tunnels — 4 cells up from bottom (row = ROWS-1-4 = 9)
        warp_row = ROWS - 1 - 4
        self.grid[warp_row][0] = WARP_L
        self.grid[warp_row][COLS - 1] = WARP_R
        self.warp_row = warp_row

        self._dirty = True

    # ── Collision helpers ────────────────────────────────────────────────────

    def is_wall(self, col: int, row: int) -> bool:
        if col < 0 or col >= COLS or row < 0 or row >= ROWS:
            return True
        return self.grid[row][col] == WALL

    def is_warp(self, col: int, row: int) -> int:
        """Return WARP_L, WARP_R, or 0."""
        if 0 <= row < ROWS and 0 <= col < COLS:
            v = self.grid[row][col]
            if v in (WARP_L, WARP_R):
                return v
        return 0

    def cell_to_px(self, col: float, row: float):
        """Center pixel of a cell."""
        return (PLAY_X + (col + 0.5) * CELL, PLAY_Y + (row + 0.5) * CELL)

    def px_to_cell(self, x: float, y: float):
        return ((x - PLAY_X) / CELL - 0.5, (y - PLAY_Y) / CELL - 0.5)

    # ── Pathfinding helper: get open neighbors ───────────────────────────────

    def open_neighbors(self, col: int, row: int) -> list[tuple[int, int]]:
        neighbors = []
        for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nc, nr = col + dc, row + dr
            if not self.is_wall(nc, nr):
                neighbors.append((nc, nr))
        return neighbors

    # ── Render ───────────────────────────────────────────────────────────────

    def _build_surface(self):
        surf = pygame.Surface((COLS * CELL, ROWS * CELL))
        surf.fill(BG)
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
                ct = self.grid[r][c]
                if ct == WALL:
                    pygame.draw.rect(surf, WALL_EDGE, rect)
                    inner = rect.inflate(-6, -6)
                    pygame.draw.rect(surf, (0, 150, 220), inner, border_radius=4)
                    # Glow line on top/left edges
                    pygame.draw.line(surf, WALL_GLOW,
                                     (rect.left + 2, rect.top + 2),
                                     (rect.right - 2, rect.top + 2), 2)
                elif ct in (WARP_L, WARP_R):
                    pygame.draw.rect(surf, FLOOR, rect)
                    # Draw a glowing portal arch
                    color = (0, 255, 200)
                    pygame.draw.rect(surf, color, rect, 3, border_radius=8)
                    pygame.draw.rect(surf, (0, 100, 80), rect.inflate(-8, -8), border_radius=6)
                    font = pygame.font.SysFont("monospace", 10, bold=True)
                    lbl = font.render("WARP", True, color)
                    surf.blit(lbl, lbl.get_rect(center=rect.center))
                else:
                    pygame.draw.rect(surf, FLOOR, rect)
        self._wall_surf = surf
        self._dirty = False

    def draw(self, screen: pygame.Surface):
        if self._dirty or self._wall_surf is None:
            self._build_surface()
        screen.blit(self._wall_surf, (PLAY_X, PLAY_Y))
