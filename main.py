"""main.py — Entry point and event loop."""
import os
os.environ["SDL_VIDEODRIVER"] = os.environ.get("SDL_VIDEODRIVER", "")

import pygame
import sys
from src.constants import *
from src.game import Game
import src.sounds as sounds


def main():
    pygame.init()
    sounds.init()

    flags = 0
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    game = Game(num_players=1)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)  # cap dt to avoid spiral-of-death

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Title screen
                if game.state == STATE_TITLE:
                    if event.key == pygame.K_SPACE:
                        game.num_players = 1
                        game.start_game()
                    elif event.key == pygame.K_RETURN:
                        game.num_players = 2
                        game.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                # Playing
                elif game.state == STATE_PLAYING:
                    if event.key == pygame.K_SPACE:
                        game.player_shoot(1)
                    elif event.key == pygame.K_RETURN:
                        if game.num_players >= 2:
                            game.player_shoot(2)
                    elif event.key == pygame.K_ESCAPE:
                        game.state = STATE_TITLE
                    # Respawn on movement keys when dead
                    elif event.key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
                        game.player_respawn(1)
                    elif event.key in (pygame.K_UP, pygame.K_DOWN,
                                        pygame.K_LEFT, pygame.K_RIGHT):
                        game.player_respawn(2)
                    # Debug: skip dungeon
                    elif event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        game.state = STATE_BETWEEN
                        game._between_timer = 0.1

                # Game over
                elif game.state == STATE_GAMEOVER:
                    if event.key == pygame.K_SPACE:
                        game = Game(game.num_players)
                        game.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        game = Game(1)
                        game.state = STATE_TITLE

        game.update(dt, keys)

        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
