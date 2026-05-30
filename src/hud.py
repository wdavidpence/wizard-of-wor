"""hud.py — Heads-up display: scores, lives, dungeon, status messages."""
import pygame
from src.constants import *


class HUD:
    def __init__(self):
        self._font_lg = None
        self._font_sm = None
        self._font_xs = None
        self._msg_text = ""
        self._msg_timer = 0.0
        self._msg_color = WHITE

    def _ensure_fonts(self):
        if self._font_lg is None:
            self._font_lg = pygame.font.SysFont("monospace", 28, bold=True)
            self._font_sm = pygame.font.SysFont("monospace", 16, bold=True)
            self._font_xs = pygame.font.SysFont("monospace", 12)

    def show_message(self, text: str, color=WHITE, duration: float = 2.5):
        self._msg_text  = text
        self._msg_timer = duration
        self._msg_color = color

    def update(self, dt: float):
        if self._msg_timer > 0:
            self._msg_timer -= dt

    def draw(self, screen: pygame.Surface, players: list, dungeon: int,
             heartbeat_bpm: float = 60):
        self._ensure_fonts()

        # Top bar background
        pygame.draw.rect(screen, HUD_BG, (0, 0, SCREEN_W, PLAY_Y))
        pygame.draw.line(screen, CYAN, (0, PLAY_Y - 2), (SCREEN_W, PLAY_Y - 2), 2)

        # Title center
        title = self._font_sm.render("WIZARD  OF  WOR", True, WIZARD_C)
        screen.blit(title, title.get_rect(centerx=SCREEN_W // 2, y=8))

        # P1 score (left)
        if len(players) >= 1:
            p = players[0]
            sc = self._font_lg.render(f"{p.score:07d}", True, P1_COLOR)
            screen.blit(sc, (20, 4))
            lbl = self._font_xs.render("P1", True, P1_COLOR)
            screen.blit(lbl, (20, 34))
            # Lives display
            for i in range(p.lives):
                self._draw_life_icon(screen, 20 + i * 18, 34, P1_COLOR)

        # P2 score (right) if present
        if len(players) >= 2:
            p2 = players[1]
            sc2 = self._font_lg.render(f"{p2.score:07d}", True, P2_COLOR)
            screen.blit(sc2, (SCREEN_W - sc2.get_width() - 20, 4))
            lbl2 = self._font_xs.render("P2", True, P2_COLOR)
            screen.blit(lbl2, (SCREEN_W - 40, 34))
            for i in range(p2.lives):
                self._draw_life_icon(screen, SCREEN_W - 20 - (i + 1) * 18, 34, P2_COLOR)

        # Center flash message
        if self._msg_timer > 0:
            alpha = min(1.0, self._msg_timer / 0.4)
            c = tuple(int(v * alpha) for v in self._msg_color)
            msg = self._font_sm.render(self._msg_text, True, c)
            mx = SCREEN_W // 2 - msg.get_width() // 2
            my = PLAY_Y + ROWS * CELL // 2 - 14
            # Dark backdrop
            pad = pygame.Rect(mx - 10, my - 6, msg.get_width() + 20, msg.get_height() + 12)
            bg = pygame.Surface(pad.size, pygame.SRCALPHA)
            bg.fill((0, 0, 30, 180))
            screen.blit(bg, pad.topleft)
            screen.blit(msg, (mx, my))

        # Heartbeat indicator (bottom right of HUD bar)
        bpm_lbl = self._font_xs.render(f"♥ {int(heartbeat_bpm)}", True,
                                        (180, 60, 60) if heartbeat_bpm > 120 else (100, 60, 80))
        screen.blit(bpm_lbl, (SCREEN_W - 60, 4))

    def _draw_life_icon(self, screen, x, y, color):
        """Tiny Worrior silhouette for lives."""
        pygame.draw.rect(screen, color, (x, y + 4, 12, 14), border_radius=2)
        pygame.draw.rect(screen, CYAN, (x + 1, y + 5, 10, 5), border_radius=1)
