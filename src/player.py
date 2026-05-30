"""player.py — Worrior player character."""
import pygame
from src.constants import *
from src.maze import WARP_L, WARP_R
from src.bullet import Bullet


class Player:
    def __init__(self, player_id: int, start_col: float, start_row: float):
        self.pid    = player_id        # 1 or 2
        self.col    = float(start_col)
        self.row    = float(start_row)
        self.facing = "right" if player_id == 1 else "left"
        self.color  = P1_COLOR if player_id == 1 else P2_COLOR
        self.lives  = PLAYER_LIVES
        self.score  = 0
        self.alive  = True
        self.active = True             # has been placed in dungeon

        self._bullet: Bullet | None = None
        self._invuln = 0.0             # invulnerability timer (sec)
        self._death_anim = 0.0
        self._respawn_pending = False
        self._blink = 0.0

        # Movement
        self._vx = 0.0
        self._vy = 0.0
        self._target_col: float | None = None
        self._target_row: float | None = None

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, keys, maze):
        if not self.alive or self._invuln > 0 and not self.alive:
            return

        if self.pid == 1:
            up    = keys[pygame.K_w]
            down  = keys[pygame.K_s]
            left  = keys[pygame.K_a]
            right = keys[pygame.K_d]
        else:
            up    = keys[pygame.K_UP]
            down  = keys[pygame.K_DOWN]
            left  = keys[pygame.K_LEFT]
            right = keys[pygame.K_RIGHT]

        dx, dy = 0, 0
        if right: dx, dy = 1, 0;  self.facing = "right"
        elif left:  dx, dy = -1, 0; self.facing = "left"
        elif up:    dx, dy = 0, -1; self.facing = "up"
        elif down:  dx, dy = 0, 1;  self.facing = "down"

        self._vx = dx * PLAYER_SPEED
        self._vy = dy * PLAYER_SPEED

    def try_shoot(self, maze) -> Bullet | None:
        if not self.alive:
            return None
        if self._bullet and self._bullet.alive:
            return None  # one shot on screen rule
        color = BULLET_COLOR_P1 if self.pid == 1 else BULLET_COLOR_P2
        self._bullet = Bullet(self.col, self.row, self.facing, color,
                              owner=f"p{self.pid}")
        return self._bullet

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, maze):
        if self._invuln > 0:
            self._invuln -= dt
            self._blink += dt

        if not self.alive:
            return

        # Move with wall collision
        nc = self.col + self._vx * dt
        nr = self.row + self._vy * dt
        ic, ir = int(nc + 0.5), int(nr + 0.5)

        # Horizontal
        if self._vx != 0 and not maze.is_wall(int(nc + 0.5), int(self.row + 0.5)):
            self.col = nc
        # Vertical
        if self._vy != 0 and not maze.is_wall(int(self.col + 0.5), int(nr + 0.5)):
            self.row = nr

        # Clamp to playfield
        self.col = max(0.5, min(COLS - 1.5, self.col))
        self.row = max(0.5, min(ROWS - 1.5, self.row))

        # Warp tunnels
        wt = maze.is_warp(int(self.col + 0.5), int(self.row + 0.5))
        if wt == WARP_L:
            self.col = COLS - 2.0
        elif wt == WARP_R:
            self.col = 1.0

        # Update bullet
        if self._bullet and self._bullet.alive:
            self._bullet.update(dt, maze)

    def kill(self):
        self.lives -= 1
        self.alive = False
        self._invuln = RESPAWN_DELAY
        self._respawn_pending = True

    def respawn(self, col: float, row: float):
        self.col = col
        self.row = row
        self.alive = True
        self._invuln = RESPAWN_DELAY
        self._respawn_pending = False
        self._bullet = None

    def is_invulnerable(self) -> bool:
        return self._invuln > 0

    # ── Radar dot ─────────────────────────────────────────────────────────────

    def get_radar_pos(self) -> tuple[float, float]:
        """Normalized position 0-1."""
        return (self.col / COLS, self.row / ROWS)

    # ── Render ────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return
        # Blink during invuln
        if self._invuln > 0 and int(self._blink * 8) % 2:
            return

        cx = int(PLAY_X + self.col * CELL)
        cy = int(PLAY_Y + self.row * CELL)
        self._draw_sprite(screen, cx, cy)

        # Draw bullet
        if self._bullet and self._bullet.alive:
            self._bullet.draw(screen)

    def _draw_sprite(self, screen, cx, cy):
        """Draw a futuristic space-marine silhouette."""
        c = self.color
        dim = (max(0, c[0]-80), max(0, c[1]-80), max(0, c[2]-80))

        # Body (helmet + torso)
        body = pygame.Rect(cx - 10, cy - 14, 20, 28)
        pygame.draw.rect(screen, dim, body, border_radius=5)
        pygame.draw.rect(screen, c, body.inflate(-4, -4), border_radius=4)

        # Visor
        visor = pygame.Rect(cx - 7, cy - 12, 14, 8)
        pygame.draw.rect(screen, CYAN, visor, border_radius=3)

        # Gun barrel — direction dependent
        if self.facing == "right":
            pygame.draw.rect(screen, c, (cx + 10, cy - 2, 12, 4), border_radius=2)
        elif self.facing == "left":
            pygame.draw.rect(screen, c, (cx - 22, cy - 2, 12, 4), border_radius=2)
        elif self.facing == "up":
            pygame.draw.rect(screen, c, (cx - 2, cy - 26, 4, 12), border_radius=2)
        elif self.facing == "down":
            pygame.draw.rect(screen, c, (cx - 2, cy + 14, 4, 12), border_radius=2)

        # Neon outline
        pygame.draw.rect(screen, c, body, 1, border_radius=5)
