"""enemy.py — All enemy types with AI, invisibility, and rendering."""
import pygame
import random
import math
from src.constants import *
from src.maze import WARP_L, WARP_R
from src.bullet import Bullet


class Enemy:
    """Base enemy class."""

    SHOT_COOLDOWN = 2.5  # seconds between shots

    def __init__(self, col: float, row: float, etype: str):
        self.col   = float(col)
        self.row   = float(row)
        self.etype = etype
        self.alive = True
        self.facing = random.choice(["left", "right", "up", "down"])
        self._shot_timer  = random.uniform(1.0, self.SHOT_COOLDOWN)
        self._move_timer  = 0.0
        self._change_dir  = random.uniform(0.5, 1.5)
        self._bullet: Bullet | None = None
        self._vis_timer   = 0.0    # for Garwor flicker
        self.invisible    = False

        self.speed  = BURWOR_SPEED
        self.color  = BURWOR_C
        self.points = BURWOR_PTS
        self._anim  = 0.0          # animation phase

    # ── AI movement (simple grid-seeking) ────────────────────────────────────

    def _choose_direction(self, maze, target_col: float = None, target_row: float = None):
        """Pick a valid direction, optionally biasing toward target."""
        ic, ir = int(self.col + 0.5), int(self.row + 0.5)
        neighbors = maze.open_neighbors(ic, ir)
        if not neighbors:
            return
        if target_col is not None:
            # Prefer direction toward target
            dx = target_col - self.col
            dy = target_row - self.row
            best = None
            best_dot = -999
            for nc, nr in neighbors:
                ndx, ndy = nc - ic, nr - ir
                dot = ndx * dx + ndy * dy
                if dot > best_dot:
                    best_dot = dot
                    best = (nc, nr)
            # 30% random to avoid deadlocks
            if random.random() < 0.3:
                best = random.choice(neighbors)
        else:
            best = random.choice(neighbors)

        if best:
            dc, dr = best[0] - ic, best[1] - ir
            if dc == 1:   self.facing = "right"
            elif dc == -1: self.facing = "left"
            elif dr == 1:  self.facing = "down"
            elif dr == -1: self.facing = "up"

    def _explode_on_wall(self, maze, particles, cell_size: int = CELL):
        """Spawn particles where the bullet would hit the wall."""
        ic, ir = int(self.col + 0.5), int(self.row + 0.5)
        px = PLAY_X + ic * cell_size
        py = PLAY_Y + ir * cell_size
        # Slightly offset towards the side of the wall hit
        if self.facing == "right":
            px += cell_size - 8
        elif self.facing == "left":
            px += 8
        elif self.facing == "down":
            py += cell_size - 8
        elif self.facing == "up":
            py += 8
        particles.explode(int(px), int(py), WALL, 8)

    def _move(self, dt: float, maze, tx=None, ty=None):
        """Cell-anchored movement: snap to grid, move straight, pick new direction when blocked."""
        DIRS = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}
        dc, dr = DIRS[self.facing]

        # 1) Snap to nearest cell center — prevents drift
        ic, ir = int(self.col + 0.5), int(self.row + 0.5)
        self.col = float(ic) + 0.5
        self.row = float(ir) + 0.5

        # 2) Move one step forward in current facing direction
        nc = self.col + dc * self.speed * dt
        nr = self.row + dr * self.speed * dt

        # 3) Check if the next cell is a wall
        nc_col = int(nc + 0.5)
        nc_row = int(nr + 0.5)

        if maze.is_wall(nc_col, nc_row):
            # Hit a wall: stay centered, pick new direction
            self._choose_direction(maze, tx, ty)
            return

        # 4) Move to new position
        self.col = nc
        self.row = nr

        # 5) Warp tunnels
        wt = maze.is_warp(int(self.col + 0.5), int(self.row + 0.5))
        if wt == WARP_L:
            self.col = COLS - 2.0
        elif wt == WARP_R:
            self.col = 1.0

        # 6) Periodic direction change — only when near a cell center to prevent diagonal drift
        dist_from_center = abs(self.col - (int(self.col + 0.5) + 0.5)) + abs(self.row - (int(self.row + 0.5) + 0.5))
        self._change_dir -= dt
        if self._change_dir <= 0 and dist_from_center < 0.4:
            self._change_dir = random.uniform(0.8, 2.5)
            if random.random() < 0.4:
                self._choose_direction(maze, tx, ty)

    def _try_shoot(self, dt: float) -> Bullet | None:
        self._shot_timer -= dt
        if self._shot_timer <= 0:
            self._shot_timer = self.SHOT_COOLDOWN * random.uniform(0.7, 1.3)
            return Bullet(self.col, self.row, self.facing,
                          BULLET_COLOR_E, owner="enemy")
        return None

    def update(self, dt: float, maze, players: list):
        """Return list of bullets (single or spread)."""
        if not self.alive:
            return []
        self._anim += dt

        # Find nearest live player for targeting
        tx, ty = None, None
        live = [p for p in players if p.alive]
        if live:
            p = min(live, key=lambda p: abs(p.col - self.col) + abs(p.row - self.row))
            tx, ty = p.col, p.row

        self._move(dt, maze, tx, ty)
        shot = self._try_shoot(dt)
        return [shot] if shot else []

    def kill(self):
        self.alive = False

    def get_radar_pos(self) -> tuple[float, float]:
        return (self.col / COLS, self.row / ROWS)

    # ── Render ────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return
        if self.invisible:
            return
        cx = int(PLAY_X + self.col * CELL)
        cy = int(PLAY_Y + self.row * CELL)
        self._draw_shape(screen, cx, cy)

    def _draw_shape(self, screen, cx, cy):
        """Generic enemy shape — override in subclasses."""
        c = self.color
        pulse = int(20 * math.sin(self._anim * 4))
        c2 = tuple(min(255, v + pulse) for v in c)
        pygame.draw.polygon(screen, c2, [
            (cx, cy - 16), (cx + 14, cy + 12), (cx - 14, cy + 12)
        ])
        pygame.draw.polygon(screen, c, [
            (cx, cy - 16), (cx + 14, cy + 12), (cx - 14, cy + 12)
        ], 2)


# ── Burwor ────────────────────────────────────────────────────────────────────

class Burwor(Enemy):
    SHOT_COOLDOWN = 3.0

    def __init__(self, col, row):
        super().__init__(col, row, "burwor")
        self.speed  = BURWOR_SPEED
        self.color  = BURWOR_C
        self.points = BURWOR_PTS

    def _draw_shape(self, screen, cx, cy):
        c = self.color
        pulse = int(15 * math.sin(self._anim * 3))
        c2 = tuple(min(255, v + pulse) for v in c)
        # Wolf-like head: ears + snout
        # Body
        pygame.draw.ellipse(screen, c2, (cx - 14, cy - 10, 28, 22))
        # Ears
        pygame.draw.polygon(screen, c, [(cx - 10, cy - 10), (cx - 16, cy - 22), (cx - 4, cy - 10)])
        pygame.draw.polygon(screen, c, [(cx + 10, cy - 10), (cx + 16, cy - 22), (cx + 4, cy - 10)])
        # Eyes
        pygame.draw.circle(screen, CYAN, (cx - 5, cy - 4), 3)
        pygame.draw.circle(screen, CYAN, (cx + 5, cy - 4), 3)
        # Snout
        pygame.draw.ellipse(screen, (200, 200, 255), (cx - 6, cy + 4, 12, 8))


# ── Garwor ────────────────────────────────────────────────────────────────────

class Garwor(Enemy):
    SHOT_COOLDOWN = 2.5
    INVIS_CYCLE   = 3.0   # seconds before going invisible
    FLICKER_TIME  = 0.5   # flicker duration before disappearing

    def __init__(self, col, row):
        super().__init__(col, row, "garwor")
        self.speed   = GARWOR_SPEED
        self.color   = GARWOR_C
        self.points  = GARWOR_PTS
        self._vis    = self.INVIS_CYCLE   # visible timer
        self._flicker = False
        self.invisible = False

    def update(self, dt, maze, players):
        if not self.alive:
            return None
        # Visibility cycling
        self._vis -= dt
        if self._vis <= 0:
            if not self.invisible:
                if not self._flicker:
                    self._flicker = True
                    self._vis = self.FLICKER_TIME
                else:
                    self.invisible = True
                    self._flicker = False
                    self._vis = self.INVIS_CYCLE * 2
            else:
                self.invisible = False
                self._vis = self.INVIS_CYCLE

        return super().update(dt, maze, players)

    def draw(self, screen):
        if not self.alive:
            return
        if self.invisible and not self._flicker:
            return
        cx = int(PLAY_X + self.col * CELL)
        cy = int(PLAY_Y + self.row * CELL)
        alpha = 255
        if self._flicker:
            alpha = int(128 + 127 * math.sin(self._anim * 20))
        c = tuple(int(v * alpha / 255) for v in self.color)
        self._draw_garwor(screen, cx, cy, c)

    def _draw_garwor(self, screen, cx, cy, c):
        # T-rex-like shape
        pygame.draw.rect(screen, c, (cx - 10, cy - 16, 20, 24), border_radius=4)
        # Big jaw
        pygame.draw.polygon(screen, c, [(cx - 12, cy + 4), (cx + 12, cy + 4),
                                         (cx + 8, cy + 16), (cx - 8, cy + 16)])
        # Eyes glowing
        eye_c = tuple(min(255, v + 100) for v in c)
        pygame.draw.circle(screen, eye_c, (cx - 6, cy - 8), 4)
        pygame.draw.circle(screen, eye_c, (cx + 6, cy - 8), 4)
        pygame.draw.circle(screen, (255, 255, 200), (cx - 6, cy - 8), 2)
        pygame.draw.circle(screen, (255, 255, 200), (cx + 6, cy - 8), 2)


# ── Thorwor ───────────────────────────────────────────────────────────────────

class Thorwor(Enemy):
    SHOT_COOLDOWN = 2.0

    def __init__(self, col, row):
        super().__init__(col, row, "thorwor")
        self.speed     = THORWOR_SPEED
        self.color     = THORWOR_C
        self.points    = THORWOR_PTS
        self.invisible = True   # always invisible (radar only)

    def update(self, dt, maze, players):
        # Brief flash before shooting
        fire_list = super().update(dt, maze, players)
        if fire_list:
            self.invisible = False
            self._vis_timer = 0.3
        self._vis_timer = max(0, self._vis_timer - dt)
        if self._vis_timer <= 0:
            self.invisible = True
        return fire_list

    def _draw_shape(self, screen, cx, cy):
        # Demon-like shape when briefly visible
        c = (255, 80, 80)
        pygame.draw.polygon(screen, c, [
            (cx, cy - 18), (cx + 12, cy - 4),
            (cx + 16, cy + 12), (cx, cy + 6),
            (cx - 16, cy + 12), (cx - 12, cy - 4)
        ])
        pygame.draw.circle(screen, (255, 200, 0), (cx - 5, cy - 4), 3)
        pygame.draw.circle(screen, (255, 200, 0), (cx + 5, cy - 4), 3)


# ── Worluk ────────────────────────────────────────────────────────────────────

class Worluk(Enemy):
    def __init__(self, col, row):
        super().__init__(col, row, "worluk")
        self.speed     = WORLUK_SPEED
        self.color     = WORLUK_C
        self.points    = WORLUK_PTS
        self.invisible = False
        self._flee_dir = random.choice(["left", "right"])
        self.facing    = self._flee_dir
        self._wing_anim = 0.0

    def update(self, dt, maze, players):
        """Worluk flees toward nearest warp tunnel — no shooting."""
        if not self.alive:
            return None
        self._anim += dt
        self._wing_anim += dt

        # Always head for a warp tunnel
        target_col = 0.5 if self._flee_dir == "left" else COLS - 1.5
        target_row = float(maze.warp_row)

        self._move(dt, maze, target_col, target_row)
        return None   # Worluk does NOT shoot

    def _draw_shape(self, screen, cx, cy):
        # Butterfly/moth silhouette
        w = int(8 + 6 * abs(math.sin(self._wing_anim * 8)))
        c = self.color
        c2 = tuple(min(255, v + 60) for v in c)
        # Wings
        pygame.draw.ellipse(screen, c, (cx - w - 14, cy - 12, w + 10, 24))
        pygame.draw.ellipse(screen, c, (cx + 4, cy - 12, w + 10, 24))
        # Body
        pygame.draw.ellipse(screen, c2, (cx - 6, cy - 14, 12, 28))
        # Eye
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy - 6), 3)


# ── Worlord miniboss (dungeon 8+) ─────────────────────────────────────────────

class Worlord(Enemy):
    """Large, slow miniboss — 2 hits, 3-bullet spread shot, bright red."""

    SHOT_COOLDOWN = 3.5
    HP            = WORLORD_LIVES

    def __init__(self, col, row):
        super().__init__(col, row, "worlord")
        self.speed   = WORLORD_SPEED
        self.color   = WORLORD_COLOR
        self.points  = WORLORD_PTS
        self.invisible = False
        self.hurt_flash = 0.0       # flash after taking damage
        self.alive    = True

    def update(self, dt, maze, players):
        if not self.alive:
            return None
        self._anim += dt
        self.hurt_flash = max(0, self.hurt_flash - dt)
        return super().update(dt, maze, players)

    def take_damage(self, dmg: int = 1):
        """Override kill to support multi-hit."""
        self.hurt_flash = 0.15
        if self.HP > 1:
            self.HP -= 1
            return True  # still alive
        self.alive = False
        return False  # died

    def _try_shoot(self, dt: float):
        """Override to shoot a 3-bullet spread."""
        self._shot_timer -= dt
        if self._shot_timer <= 0:
            self._shot_timer = self.SHOT_COOLDOWN * random.uniform(0.7, 1.3)
            bullets = []
            # Spread: left (-1), center (0), right (+1) in facing direction
            spread_offsets = [-1, 0, 1]
            for off in spread_offsets:
                dir_name = self.facing
                if off != 0:
                    # Convert to the adjacent axis direction
                    if self.facing == "right":
                        dir_name = "down" if off < 0 else "up"
                    elif self.facing == "left":
                        dir_name = "down" if off < 0 else "up"
                    elif self.facing == "up":
                        dir_name = "left" if off < 0 else "right"
                    elif self.facing == "down":
                        dir_name = "left" if off < 0 else "right"
                b = Bullet(self.col, self.row, dir_name,
                           BULLET_COLOR_E, owner="enemy")
                bullets.append(b)
            return bullets
        return None

    def draw(self, screen):
        if not self.alive:
            return
        cx = int(PLAY_X + self.col * CELL)
        cy = int(PLAY_Y + self.row * CELL)
        self._draw_shape(screen, cx, cy)

    def _draw_shape(self, screen, cx, cy):
        """Gargantuan red boss with crown-like spikes."""
        base_color = self.color
        if self.hurt_flash > 0:
            base_color = (255, 255, 255)  # white flash
        else:
            pulse = int(20 * math.sin(self._anim * 3))
            base_color = tuple(min(255, v + pulse) for v in self.color)

        # Main body — larger than normal enemy
        big = pygame.Rect(cx - 22, cy - 22, 44, 44)
        pygame.draw.rect(screen, base_color, big, border_radius=8)
        pygame.draw.rect(screen, (255, 100, 100), big.inflate(-6, -6), border_radius=6)

        # Crown spikes
        spike_y = cy - 28
        for dx in [-18, -6, 6, 18]:
            pygame.draw.polygon(screen, (255, 150, 50), [
                (cx + dx, spike_y),
                (cx + dx - 4, spike_y - 12),
                (cx + dx + 4, spike_y - 12),
            ])

        # Eyes — menacing
        pygame.draw.circle(screen, (255, 255, 0), (cx - 8, cy - 6), 5)
        pygame.draw.circle(screen, (255, 255, 0), (cx + 8, cy - 6), 5)
        pygame.draw.circle(screen, (200, 0, 0), (cx - 8, cy - 6), 2)
        pygame.draw.circle(screen, (200, 0, 0), (cx + 8, cy - 6), 2)

        # Mouth — jagged
        pygame.draw.polygon(screen, (80, 0, 0), [
            (cx - 14, cy + 8), (cx - 10, cy + 14), (cx - 4, cy + 10),
            (cx, cy + 16), (cx + 4, cy + 10), (cx + 10, cy + 14),
            (cx + 14, cy + 8),
        ])

        # Border glow
        pygame.draw.rect(screen, (255, 80, 80), big, 2, border_radius=8)


# ── Wizard of Wor ─────────────────────────────────────────────────────────────

class WizardOfWor(Enemy):
    TELEPORT_INTERVAL = 2.5
    SHOT_COOLDOWN     = 1.8

    def __init__(self, col, row):
        super().__init__(col, row, "wizard")
        self.speed    = 0
        self.color    = WIZARD_C
        self.points   = WIZARD_PTS
        self._teleport_timer = self.TELEPORT_INTERVAL
        self._taunt_text = ""
        self._taunt_timer = 0.0
        self.invisible = False

    def set_taunt(self, text: str):
        self._taunt_text = text
        self._taunt_timer = 3.0

    def update(self, dt, maze, players):
        if not self.alive:
            return None
        self._anim += dt

        # Teleport randomly
        self._teleport_timer -= dt
        if self._teleport_timer <= 0:
            self._teleport_timer = self.TELEPORT_INTERVAL * random.uniform(0.7, 1.3)
            self._teleport(maze)

        self._taunt_timer = max(0, self._taunt_timer - dt)
        return self._try_shoot(dt)

    def _teleport(self, maze):
        for _ in range(30):
            nc = random.randint(1, COLS - 2)
            nr = random.randint(1, ROWS - 2)
            if not maze.is_wall(nc, nr):
                self.col = float(nc)
                self.row = float(nr)
                break

    def _draw_shape(self, screen, cx, cy):
        c = self.color
        pulse = int(30 * math.sin(self._anim * 5))
        c2 = tuple(min(255, v + pulse) for v in c)

        # Robes
        pygame.draw.polygon(screen, c2, [
            (cx, cy - 20), (cx + 18, cy + 16), (cx - 18, cy + 16)
        ])
        # Hood
        pygame.draw.circle(screen, c, (cx, cy - 20), 12)
        # Face — glowing eyes
        pygame.draw.circle(screen, (255, 255, 100), (cx - 5, cy - 22), 3)
        pygame.draw.circle(screen, (255, 255, 100), (cx + 5, cy - 22), 3)
        # Staff
        pygame.draw.line(screen, CYAN, (cx + 18, cy + 16), (cx + 22, cy - 16), 3)
        pygame.draw.circle(screen, (200, 255, 255), (cx + 22, cy - 16), 5)
        # Taunt text
        if self._taunt_timer > 0 and self._taunt_text:
            font = pygame.font.SysFont("monospace", 11, bold=True)
            txt = font.render(self._taunt_text, True, (255, 255, 100))
            screen.blit(txt, (cx - txt.get_width() // 2, cy - 44))
