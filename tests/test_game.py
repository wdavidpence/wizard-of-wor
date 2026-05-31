"""test_game.py — 600-frame smoke test for Wizard of WOR.

Verifies:
  - Game runs 600 frames without crashing
  - Player movement and shooting work
  - Enemies die when shot (stationary target in pit dungeon)
  - Score increases after kills
  - Bullet wall-explode particles spawn
  - Worlord spawns in dungeon 8+
  - Auto-respawn works
  - No unhandled exceptions
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import sys
import pygame
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.constants import *
from src.game import Game
from src.enemy import Burwor, Worlord


class MutableKeys:
    """Mutable keys object supporting keys[k] and keys[k] = v."""

    def __init__(self, pressed: set):
        self._pressed = set(pressed)

    def __getitem__(self, k):
        return k in self._pressed

    def __setitem__(self, k, v):
        if v:
            self._pressed.add(k)
        else:
            self._pressed.discard(k)


class WizardOfWORSmokeTest(unittest.TestCase):
    """Run the game headless for 600 frames with simulated input."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.clock = pygame.time.Clock()
        cls.surface = pygame.Surface((SCREEN_W, SCREEN_H))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def _tick(self, game, keys, n_frames=60):
        for _ in range(n_frames):
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)
            game.update(dt, keys)
            game.draw(self.surface)

    def _make_game(self, dungeon=1):
        game = Game(num_players=1)
        game.dungeon = dungeon
        game.start_game()
        game._load_dungeon(dungeon)
        return game

    def test_600_frames_no_crash(self):
        """The game should run 600 frames without exceptions."""
        game = Game(num_players=1)
        game.start_game()

        for frame in range(600):
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)

            cycle = frame % 120
            key_set = set()
            if cycle < 30:
                key_set.add(pygame.K_s)
            elif cycle < 60:
                key_set.add(pygame.K_d)
            elif cycle < 90:
                key_set.add(pygame.K_w)
            else:
                key_set.add(pygame.K_a)

            if frame % 15 == 0:
                game.player_shoot(1)

            if not game.players[0].alive:
                key_set.update([pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d])

            keys = MutableKeys(key_set)

            try:
                game.update(dt, keys)
                game.draw(self.surface)
            except Exception as exc:
                self.fail(f"Game crashed on frame {frame + 1}: {exc}")

    def test_enemies_die_when_shot(self):
        """Shoot a stationary enemy in a pit dungeon (no walls to block or confuse)."""
        game = self._make_game(13)  # Pit dungeon — no interior walls
        p = game.players[0]

        # Place enemy directly in front of player on same row
        # Player starts at col 11, row 7 in Pit dungeon
        # Put enemy at col 6 (same row), player faces left toward it
        # Freeze enemy in place by overriding _move (no AI during test)
        enemy = Burwor(6.0, 7.0)
        enemy._move = lambda dt, maze, tx=None, ty=None: None  # freeze in place
        game.enemies.append(enemy)
        p.facing = "left"
        p.col = 11.0
        p.row = 7.0

        # Fire bullets for 60 frames — enemy should be hit
        surface = pygame.Surface((SCREEN_W, SCREEN_H))
        keys = MutableKeys(set())

        for frame in range(60):
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)

            if frame % 5 == 0:
                game.player_shoot(1)

            game.update(dt, keys)
            game.draw(surface)

        # Enemy should have been hit (bullets travel fast, enemy stays put)
        self.assertTrue(not enemy.alive,
                        f"Enemy should be dead after shooting. Alive={enemy.alive}, "
                        f"score={p.score}, bullets={len(game.bullets)}")

    def test_score_increases_on_kill(self):
        """Kill an enemy and verify score goes up."""
        game = self._make_game(13)
        p = game.players[0]
        enemy = Burwor(6.0, 7.0)
        enemy._move = lambda dt, maze, tx=None, ty=None: None  # freeze in place
        game.enemies.append(enemy)
        p.facing = "left"
        p.col = 11.0
        p.row = 7.0
        initial_score = p.score

        surface = pygame.Surface((SCREEN_W, SCREEN_H))
        keys = MutableKeys(set())

        for frame in range(60):
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)
            if frame % 5 == 0:
                game.player_shoot(1)
            game.update(dt, keys)
            game.draw(surface)

        self.assertGreater(p.score, initial_score,
                           "Score should increase after killing enemy")

    def test_bullet_wall_explode_particles(self):
        """Bullets that hit walls should spawn wall-explode particles."""
        game = self._make_game(1)  # Standard dungeon with walls
        p = game.players[0]

        # Get original particle count
        initial_particles = len(game.particles._particles)

        # Fire a bullet that will definitely hit a wall (shoot sideways in standard dungeon)
        p.facing = "right"
        for _ in range(30):
            dt = 1/60
            if game.particles._particles == initial_particles or len(game.particles._particles) <= initial_particles + 5:
                game.player_shoot(1)
            game.update(dt, MutableKeys(set()))

        # Wall-explode should have created particles (small burst at wall impact)
        new_particles = len(game.particles._particles)
        # At least some new particles should exist from wall impacts
        self.assertGreater(new_particles, initial_particles,
                           "Bullet wall hits should spawn particles")

    def test_worlord_spawn(self):
        """Worlord should spawn in dungeon 8+."""
        game = self._make_game(8)
        has_worlord = any(e.etype == "worlord" for e in game.enemies)
        self.assertTrue(has_worlord,
                        "Worlord should spawn in dungeon 8+")

    def test_auto_respawn(self):
        """After a player dies, they should auto-respawn."""
        game = self._make_game(1)
        p = game.players[0]

        # Manually kill the player (simulating being hit by enemy bullet)
        p.col = 5.0
        p.row = 7.0
        p.kill()  # sets alive=False, decrements lives
        p.lives = 2  # leave at least 1 life so auto-respawn can trigger

        surface = pygame.Surface((SCREEN_W, SCREEN_H))
        keys = MutableKeys(set())

        # Wait for respawn timeout (AUTO_RESPAWN_AFTER = 2.0 seconds = 120 frames at 60fps)
        for frame in range(130):
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)
            game.update(dt, keys)
            game.draw(surface)

        self.assertTrue(p.alive,
                        "Player should auto-respawn after death timeout")


if __name__ == "__main__":
    unittest.main()
