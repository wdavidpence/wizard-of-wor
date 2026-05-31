"""game.py — Main game state machine, dungeon management, spawn sequencer."""
import pygame
import random
import math
import json
import os
from src.constants import *
from src.maze import Maze
from src.player import Player
from src.enemy import Burwor, Garwor, Thorwor, Worluk, WizardOfWor, Worlord
from src.bullet import Bullet
from src.radar import Radar
from src.hud import HUD
from src.particles import ParticleSystem
import src.sounds as sounds


class Game:
    def __init__(self, num_players: int = 1):
        self.num_players   = num_players
        self.state         = STATE_TITLE
        self.dungeon       = 1
        self.double_score  = False
        self._between_timer = 0.0
        self._title_blink  = 0.0
        self._screenshake  = 0.0
        self._shake_offset = (0, 0)

        # Hit-freeze & flash effects (arcade feel)
        self._freeze        = 0.0     # remaining freeze time
        self._freeze_speed  = 1.0     # speed multiplier (1.0 = normal, 0.5 = slow)
        self._flash         = 0.0     # remaining flash time
        self._flash_alpha   = FLASH_ALPHA

        self.maze      = Maze(1)
        self.players   = []
        self.enemies: list = []
        self.bullets: list[Bullet] = []
        self.radar     = Radar()
        self.hud       = HUD()
        self.particles = ParticleSystem()
        self.heartbeat = sounds.Heartbeat()

        self._spawn_seq_timer = 0.0
        self._spawn_phase     = 0   # 0=burwors, 1=garwors, 2=thorwors
        self._total_enemies_spawned = 0
        self._worluk_spawned  = False
        self._wizard_spawned  = False
        self._wizard_active   = False

        # High score
        self._hiscore = self._load_hiscore()
        self._game_over_timer = 0.0
        self._go_displayed = False

    # ── High score ────────────────────────────────────────────────────────────

    def _load_hiscore(self) -> int:
        try:
            p = "/root/wizard_of_wor/hiscore.json"
            if os.path.exists(p):
                return json.load(open(p))["hiscore"]
        except Exception:
            pass
        return 0

    def _save_hiscore(self):
        top = max(p.score for p in self.players) if self.players else 0
        if top > self._hiscore:
            self._hiscore = top
            json.dump({"hiscore": top}, open("/root/wizard_of_wor/hiscore.json", "w"))

    # ── Start / reset ─────────────────────────────────────────────────────────

    def start_game(self):
        self.dungeon      = 1
        self.double_score = False
        self.state        = STATE_PLAYING
        p1 = Player(1, 2.0, float(ROWS // 2))
        self.players = [p1]
        if self.num_players >= 2:
            p2 = Player(2, float(COLS - 3), float(ROWS // 2))
            self.players.append(p2)
        self._load_dungeon(self.dungeon)

    def _get_dungeon_type(self, n: int) -> str:
        """Return a human-readable dungeon type label."""
        if n == ARENA_DUNGEON:
            return "ARENA"
        elif (n == PIT_DUNGEON) or ((n > PIT_DUNGEON) and (n - PIT_DUNGEON) % PIT_REPEAT == 0):
            return "PIT"
        elif n >= WORLORD_DUNGEON:
            return "WORLORD"
        else:
            return "STANDARD"

    def _load_dungeon(self, n: int):
        self.maze  = Maze(n)
        self.enemies = []
        self.bullets = []
        self._spawn_phase = 0
        self._total_enemies_spawned = 0
        self._worluk_spawned  = False
        self._wizard_spawned  = False
        self._wizard_active   = False
        self._spawn_seq_timer = 0.5
        self.heartbeat        = sounds.Heartbeat()

        # Reset player positions
        spawn_positions = [
            (2.0, float(ROWS // 2)),
            (float(COLS - 3), float(ROWS // 2)),
        ]
        for i, p in enumerate(self.players):
            if i < len(spawn_positions):
                sc, sr = spawn_positions[i]
                p.col, p.row = sc, sr
                p.alive = True

        # Spawn initial Burwors
        self._spawn_burwors(DUNGEON_BURWORS_START)

        # Worlord boss for dungeons 8+
        if n >= WORLORD_DUNGEON:
            c, r = self._random_spawn()
            self.enemies.append(Worlord(c, r))
            self._total_enemies_spawned += 1
            self.hud.show_message("★ WORLORD ★", WORLORD_COLOR, 2.5)
            sounds.play("death_player", 0.3)

        # Bonus life before Arena
        if n == ARENA_DUNGEON:
            for p in self.players:
                p.lives += 1
            self.hud.show_message("BONUS WORRIOR!", (100, 255, 100), 3.0)
            sounds.play("bonus_life")

        dungeon_type = self._get_dungeon_type(n)
        self.hud.show_message(f"DUNGEON  {n} [{dungeon_type}]", CYAN, 2.0)

    def _spawn_burwors(self, count: int):
        for _ in range(count):
            c, r = self._random_spawn()
            self.enemies.append(Burwor(c, r))
            self._total_enemies_spawned += 1

    def _random_spawn(self) -> tuple[float, float]:
        for _ in range(50):
            c = random.randint(2, COLS - 3)
            r = random.randint(2, ROWS - 3)
            if not self.maze.is_wall(c, r):
                # Not too close to players
                ok = True
                for p in self.players:
                    if abs(p.col - c) < 4 and abs(p.row - r) < 4:
                        ok = False
                        break
                if ok:
                    return float(c), float(r)
        return float(COLS // 2), float(ROWS // 2)

    # ── Main update ───────────────────────────────────────────────────────────

    def update(self, dt: float, keys):
        # Decay freeze / flash timers
        if self._freeze > 0:
            self._freeze -= dt
            if self._freeze <= 0:
                self._freeze_speed = 1.0

        if self._flash > 0:
            self._flash -= dt

        # Apply speed multiplier for hit-freeze
        speed = self._freeze_speed
        effective_dt = dt * speed

        if self._screenshake > 0:
            self._screenshake -= dt
            mx = int(6 * self._screenshake)
            self._shake_offset = (random.randint(-mx, mx), random.randint(-mx, mx))
        else:
            self._shake_offset = (0, 0)

        self.hud.update(dt)
        self.particles.update(dt)
        self._title_blink += dt

        if self.state == STATE_TITLE:
            self._update_title(dt, keys)
        elif self.state == STATE_PLAYING:
            if self._freeze > 0 and self._freeze_speed < 1.0:
                # Hit-freeze: skip physics (classic arcade feel)
                return
            self._update_playing(effective_dt, keys)
        elif self.state == STATE_BETWEEN:
            self._update_between(dt)
        elif self.state == STATE_GAMEOVER:
            self._update_gameover(dt, keys)

    def _update_title(self, dt: float, keys):
        pass  # handled in event processing

    def _update_gameover(self, dt: float, keys):
        self._game_over_timer -= dt

    def _update_between(self, dt: float):
        self._between_timer -= dt
        if self._between_timer <= 0:
            self.dungeon += 1
            self._load_dungeon(self.dungeon)
            self.state = STATE_PLAYING

    def _update_playing(self, dt: float, keys):
        # Auto-respawn: after death timeout, spawn player back at home position
        for p in self.players:
            if not p.alive and p.lives > 0:
                if not hasattr(p, '_death_time'):
                    p._death_time = 0.0
                p._death_time += dt
                if p._death_time >= AUTO_RESPAWN_AFTER:
                    start_col = 2.0 if p.pid == 1 else float(COLS - 3)
                    p.respawn(start_col, float(ROWS // 2))
                    sounds.play("warp", 0.4)

        # Player input + movement
        for p in self.players:
            if p.alive:
                p.handle_input(keys, self.maze)
            p.update(dt, self.maze)

        # Spawn sequencer
        self._update_spawn_seq(dt)

        # Enemy update — collect bullets (handles spread shots from Worlord)
        new_bullets = []
        for e in self.enemies:
            bullets = e.update(dt, self.maze, self.players)
            if bullets:
                if isinstance(bullets, list):
                    new_bullets.extend(bullets)
                else:
                    new_bullets.append(bullets)
                sounds.play("shot_enemy", 0.3)
        self.bullets.extend(new_bullets)

        # Bullet update — pass particles for wall explosions
        for b in self.bullets:
            b.update(dt, self.maze, self.particles)

        # Collision detection
        self._check_collisions()

        # Remove dead bullets
        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        # Check dungeon clear
        self._check_dungeon_clear()

    def _update_spawn_seq(self, dt: float):
        """Progress through Burwor → Garwor → Thorwor spawn sequence."""
        alive = [e for e in self.enemies if e.alive and e.etype not in ("worluk","wizard","worlord")]
        if len(alive) > 3:
            return  # still plenty of enemies

        self._spawn_seq_timer -= dt
        if self._spawn_seq_timer > 0:
            return

        self._spawn_seq_timer = random.uniform(2.0, 4.0)

        # Phase depends on dungeon progress
        if self._spawn_phase == 0 and len(alive) < 4:
            self._spawn_phase = 1
        elif self._spawn_phase == 1 and len(alive) < 2:
            self._spawn_phase = 2

        c, r = self._random_spawn()
        if self._spawn_phase == 0:
            self.enemies.append(Burwor(c, r))
        elif self._spawn_phase == 1:
            self.enemies.append(Garwor(c, r))
        elif self._spawn_phase == 2:
            if not self._worluk_spawned:
                self.enemies.append(Thorwor(c, r))
        self._total_enemies_spawned += 1

    def _check_collisions(self):
        for b in self.bullets:
            if not b.alive:
                continue
            br = b.get_rect()

            # Player bullets hitting enemies
            if b.owner in ("p1", "p2"):
                owner_p = next((p for p in self.players
                                if f"p{p.pid}" == b.owner), None)
                for e in self.enemies:
                    if not e.alive:
                        continue
                    er = pygame.Rect(
                        int(PLAY_X + e.col * CELL) - 14,
                        int(PLAY_Y + e.row * CELL) - 14,
                        28, 28
                    )
                    if br.colliderect(er):
                        b.alive = False

                        # Multi-hit enemies (Worlord)
                        if hasattr(e, 'HP') and e.HP > 0:
                            still_alive = e.take_damage(b.damage)
                            if still_alive:
                                self.particles.explode(
                                    int(PLAY_X + e.col * CELL),
                                    int(PLAY_Y + e.row * CELL),
                                    (255, 255, 255), 10)
                                sounds.play("shot_enemy", 0.3)
                                self._screenshake = 0.15
                                continue

                        # Enemy killed
                        e.kill()
                        pts = e.points
                        if self.double_score:
                            pts *= 2
                        if owner_p:
                            owner_p.score += pts

                        # Juice effects
                        self._flash = FLASH_DUR
                        self._freeze = HIT_FREEZE_DUR
                        self._freeze_speed = 0.5
                        cx = int(PLAY_X + e.col * CELL)
                        cy = int(PLAY_Y + e.row * CELL)
                        self.particles.explode(cx, cy, e.color, 25)
                        sounds.play("death_enemy", 0.5)
                        self.hud.show_message(f"+{pts}", e.color, 0.8)
                        self._screenshake = 0.3

                        if e.etype == "worluk":
                            self.double_score = True
                            self.hud.show_message("★ DOUBLE SCORE! ★",
                                                   (255, 220, 50), 3.0)
                        elif e.etype == "wizard":
                            sounds.play("wizard_zap", 0.7)
                            self.hud.show_message("WIZARD SLAIN!", WIZARD_C, 2.5)
                            self._trigger_dungeon_clear()
                        elif e.etype == "worlord":
                            self.hud.show_message("WORLORD VANQUISHED!",
                                                   WORLORD_COLOR, 3.0)
                            self._trigger_dungeon_clear()

                # Friendly fire (2-player)
                if len(self.players) >= 2 and owner_p:
                    other = [p for p in self.players
                             if p.pid != owner_p.pid and p.alive and not p.is_invulnerable()]
                    for op in other:
                        opr = pygame.Rect(
                            int(PLAY_X + op.col * CELL) - 10,
                            int(PLAY_Y + op.row * CELL) - 10,
                            20, 20
                        )
                        if br.colliderect(opr):
                            b.alive = False
                            op.kill()
                            owner_p.score += FRIENDLY_FIRE

                            self._flash = FLASH_DUR
                            self._freeze = HIT_FREEZE_DUR
                            self._freeze_speed = 0.5

                            self.particles.explode(
                                int(PLAY_X + op.col * CELL),
                                int(PLAY_Y + op.row * CELL),
                                op.color, 30)
                            sounds.play("death_player", 0.6)
                            self._screenshake = 0.4
                            self.hud.show_message("FRIENDLY FIRE! +1000",
                                                   (255, 100, 100), 2.0)

            # Enemy bullets hitting players
            elif b.owner == "enemy":
                for p in self.players:
                    if not p.alive or p.is_invulnerable():
                        continue
                    pr = pygame.Rect(
                        int(PLAY_X + p.col * CELL) - 10,
                        int(PLAY_Y + p.row * CELL) - 10,
                        20, 20
                    )
                    if br.colliderect(pr):
                        b.alive = False
                        p.kill()

                        self._flash = FLASH_DUR
                        self._freeze = HIT_FREEZE_DUR
                        self._freeze_speed = 0.5

                        self.particles.explode(
                            int(PLAY_X + p.col * CELL),
                            int(PLAY_Y + p.row * CELL),
                            p.color, 35)
                        sounds.play("death_player", 0.7)
                        self._screenshake = 0.5
                        self.hud.show_message(f"P{p.pid} DOWN!", RED, 1.5)
                        if p.lives <= 0:
                            self._check_game_over()

            # Bullet-bullet cancellation
            for b2 in self.bullets:
                if b2 is b or not b2.alive:
                    continue
                if b.owner != b2.owner and br.colliderect(b2.get_rect()):
                    b.alive  = False
                    b2.alive = False

    def _check_dungeon_clear(self):
        alive = [e for e in self.enemies if e.alive]
        non_special = [e for e in alive if e.etype not in ("worluk","wizard","worlord")]

        if len(non_special) == 0 and not self._worluk_spawned:
            self._spawn_worluk()

        # Worluk escaped through warp
        worluk_list = [e for e in alive if e.etype == "worluk"]
        if worluk_list:
            wl = worluk_list[0]
            wt = self.maze.is_warp(int(wl.col + 0.5), int(wl.row + 0.5))
            if wt:
                wl.kill()
                self.hud.show_message("WORLUK ESCAPED!", (180, 80, 220), 2.0)
                self._maybe_spawn_wizard()
                if not self._wizard_active:
                    self._trigger_dungeon_clear()

        # All enemies dead and Wizard spawned → dungeon clear
        if len(alive) == 0 and self._wizard_spawned:
            self._trigger_dungeon_clear()

    def _spawn_worluk(self):
        self._worluk_spawned = True
        c, r = self._random_spawn()
        self.enemies.append(Worluk(c, r))
        self.hud.show_message("GET THE WORLUK!", (200, 60, 255), 2.5)
        sounds.play("worluk", 0.6)

    def _maybe_spawn_wizard(self):
        if self._wizard_spawned or self.dungeon < 5:
            return
        if random.random() < 0.65:
            self._wizard_spawned = True
            self._wizard_active  = True
            c, r = self._random_spawn()
            w = WizardOfWor(c, r)
            w.set_taunt(random.choice(WIZARD_TAUNTS))
            self.enemies.append(w)
            sounds.play("wizard_zap", 0.7)
            self.hud.show_message("THE WIZARD APPEARS!", WIZARD_C, 3.0)

    def _trigger_dungeon_clear(self):
        """Called when Wizard killed or all enemies dead and Worluk escaped."""
        sounds.play("dungeon_clear", 0.6)
        self.state = STATE_BETWEEN
        self._between_timer = 2.5

    def _check_game_over(self):
        all_dead = all(p.lives <= 0 for p in self.players)
        if all_dead:
            self._save_hiscore()
            self.hud.show_message("GAME OVER", RED, 5.0)
            sounds.play("death_player", 0.8)
            self._game_over_timer = 4.0
            self.state = STATE_GAMEOVER

    # ── Public: player shoot ──────────────────────────────────────────────────

    def player_shoot(self, player_id: int):
        for p in self.players:
            if p.pid == player_id and p.alive:
                b = p.try_shoot(self.maze)
                if b:
                    self.bullets.append(b)
                    sfx = "shot_p1" if player_id == 1 else "shot_p2"
                    sounds.play(sfx, 0.4)

    def player_respawn(self, player_id: int):
        for p in self.players:
            if p.pid == player_id and not p.alive and p.lives > 0:
                sc = 2.0 if player_id == 1 else float(COLS - 3)
                p.respawn(sc, float(ROWS // 2))
                sounds.play("warp", 0.4)

    # ── Render ────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        ox, oy = self._shake_offset

        if self.state == STATE_TITLE:
            self._draw_title(screen)
            return

        # Apply screenshake offset via a temporary surface
        if ox or oy:
            game_surf = pygame.Surface((SCREEN_W, SCREEN_H))
            game_surf.fill(BG)
            self._draw_game(game_surf)
            screen.fill(BG)
            screen.blit(game_surf, (ox, oy))
        else:
            screen.fill(BG)
            self._draw_game(screen)

        # Screen flash overlay
        if self._flash > 0:
            flash_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, int(255 * self._flash / FLASH_DUR)))
            screen.blit(flash_surf, (0, 0))

        if self.state == STATE_GAMEOVER:
            self._draw_gameover(screen)
        elif self.state == STATE_BETWEEN:
            self._draw_between(screen)

    def _draw_game(self, surface):
        self.maze.draw(surface)

        for e in self.enemies:
            e.draw(surface)

        for p in self.players:
            p.draw(surface)

        self.particles.draw(surface)

        self.radar.draw(surface, self.players, self.enemies,
                        self.dungeon, self.double_score)

        self.hud.draw(surface, self.players, self.dungeon,
                      self.heartbeat.bpm, self._get_dungeon_type(self.dungeon))

    def _draw_title(self, screen):
        screen.fill(BG)
        font_huge = pygame.font.SysFont("monospace", 64, bold=True)
        font_med  = pygame.font.SysFont("monospace", 24, bold=True)
        font_sm   = pygame.font.SysFont("monospace", 16)

        # Pulsing title
        pulse = int(30 * math.sin(self._title_blink * 2))
        c = (200 + pulse, 60, 180 + pulse)
        t = font_huge.render("WIZARD OF WOR", True, c)
        screen.blit(t, t.get_rect(centerx=SCREEN_W//2, y=120))

        sub = font_med.render("M O D E R N  E D I T I O N", True, CYAN)
        screen.blit(sub, sub.get_rect(centerx=SCREEN_W//2, y=200))

        blink_on = int(self._title_blink * 2) % 2 == 0
        if blink_on:
            s = font_med.render("PRESS  SPACE  TO  START", True, P1_COLOR)
            screen.blit(s, s.get_rect(centerx=SCREEN_W//2, y=320))

        p2 = font_sm.render("P2: PRESS ENTER FOR 2-PLAYER", True, P2_COLOR)
        screen.blit(p2, p2.get_rect(centerx=SCREEN_W//2, y=365))

        hi = font_sm.render(f"HI-SCORE: {self._hiscore:07d}", True, SCORE_COLOR)
        screen.blit(hi, hi.get_rect(centerx=SCREEN_W//2, y=420))

        # Enemy showcase
        showcase = [
            (100, (255, 220, 50),  "BURWOR   100 PTS"),
            (200, (255, 200, 40),  "GARWOR   200 PTS"),
            (300, (255, 50, 50),   "THORWOR  500 PTS  [INVISIBLE]"),
            (400, (200, 60, 255),  "WORLUK  1000 PTS  [DOUBLE SCORE!]"),
            (500, (255, 100, 200), "WIZARD  2500 PTS"),
        ]
        for y_off, col, label in showcase:
            lf = font_sm.render(label, True, col)
            screen.blit(lf, lf.get_rect(x=SCREEN_W//2 - 180, y=480 + y_off // 4))

        # Controls
        ctrl = font_sm.render("P1: WASD + SPACE    P2: ARROWS + ENTER", True, (120, 120, 180))
        screen.blit(ctrl, ctrl.get_rect(centerx=SCREEN_W//2, y=SCREEN_H - 40))

    def _draw_between(self, screen):
        font = pygame.font.SysFont("monospace", 32, bold=True)
        t = font.render(f"ENTERING  DUNGEON  {self.dungeon + 1}", True, CYAN)
        r = t.get_rect(centerx=SCREEN_W//2, centery=SCREEN_H//2)
        bg = pygame.Surface((r.width + 40, r.height + 20), pygame.SRCALPHA)
        bg.fill((0, 0, 20, 200))
        screen.blit(bg, (r.x - 20, r.y - 10))
        screen.blit(t, r)

    def _draw_gameover(self, screen):
        font_lg = pygame.font.SysFont("monospace", 72, bold=True)
        font_sm = pygame.font.SysFont("monospace", 20)
        t = font_lg.render("GAME OVER", True, RED)
        screen.blit(t, t.get_rect(centerx=SCREEN_W//2, centery=SCREEN_H//2 - 40))
        top = max(p.score for p in self.players) if self.players else 0
        sc = font_sm.render(f"SCORE: {top:07d}   HI: {self._hiscore:07d}", True, SCORE_COLOR)
        screen.blit(sc, sc.get_rect(centerx=SCREEN_W//2, centery=SCREEN_H//2 + 30))
        s2 = font_sm.render("PRESS SPACE TO PLAY AGAIN", True, WHITE)
        screen.blit(s2, s2.get_rect(centerx=SCREEN_W//2, centery=SCREEN_H//2 + 70))
