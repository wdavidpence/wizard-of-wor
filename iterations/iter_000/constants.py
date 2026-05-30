"""constants.py — All magic numbers live here."""
import pygame

# ── Screen ────────────────────────────────────────────────────────────────────
SCREEN_W = 1280
SCREEN_H = 800
FPS      = 60
TITLE    = "WIZARD OF WOR"

# ── Grid ──────────────────────────────────────────────────────────────────────
CELL      = 48          # pixels per cell
COLS      = 22          # playfield columns
ROWS      = 14          # playfield rows
PLAY_X    = (SCREEN_W - COLS * CELL) // 2   # left edge of playfield
PLAY_Y    = 40                               # top edge (below HUD)

# ── Radar bar ─────────────────────────────────────────────────────────────────
RADAR_H   = 56
RADAR_Y   = PLAY_Y + ROWS * CELL + 4

# ── Colors (neon-on-black cyberpunk palette) ──────────────────────────────────
BLACK       = (0,   0,   0)
BG          = (4,   4,  12)          # near-black blue
WALL        = (0,  180, 255)         # cyan
WALL_EDGE   = (0,  80,  140)
WALL_GLOW   = (0,  240, 255)
FLOOR       = (6,   6,  18)

# Player colors
P1_COLOR    = (255, 220,  50)        # gold
P2_COLOR    = (100, 255, 150)        # green

# Enemy colors
BURWOR_C    = (80,  120, 255)        # blue
GARWOR_C    = (255, 200,  40)        # yellow
THORWOR_C   = (255,  50,  50)        # red
WORLUK_C    = (200,  60, 255)        # purple
WIZARD_C    = (255, 100, 200)        # pink/magenta

# UI colors
HUD_BG      = (8,   8,  24)
HUD_TEXT    = (200, 200, 255)
SCORE_COLOR = (255, 220,  50)
RADAR_BG    = (4,   4,  16)
RADAR_GRID  = (20,  20,  60)
WHITE       = (255, 255, 255)
RED         = (255,  60,  60)
GREEN       = (60,  255, 100)
CYAN        = (0,   240, 255)
PURPLE      = (160,  60, 255)

# ── Bullet ────────────────────────────────────────────────────────────────────
BULLET_SPEED   = 12    # cells per second
BULLET_COLOR_P1= (255, 255, 100)
BULLET_COLOR_P2= (100, 255, 160)
BULLET_COLOR_E = (255,  80,  80)

# ── Player ────────────────────────────────────────────────────────────────────
PLAYER_SPEED   = 5.5   # cells per second
PLAYER_LIVES   = 3
RESPAWN_DELAY  = 1.8   # seconds of invuln after respawn

# ── Enemy speeds (cells/sec) ──────────────────────────────────────────────────
BURWOR_SPEED   = 2.5
GARWOR_SPEED   = 3.5
THORWOR_SPEED  = 5.0
WORLUK_SPEED   = 7.0
WIZARD_SPEED   = 0     # teleports, doesn't walk

# ── Enemy points ─────────────────────────────────────────────────────────────
BURWOR_PTS     = 100
GARWOR_PTS     = 200
THORWOR_PTS    = 500
WORLUK_PTS     = 1000
WIZARD_PTS     = 2500
FRIENDLY_FIRE  = 1000  # shooting the other player

# ── Dungeon settings ─────────────────────────────────────────────────────────
DUNGEON_BURWORS_START = 6
ARENA_DUNGEON         = 4
PIT_DUNGEON           = 13
PIT_REPEAT            = 6
WORLORD_DUNGEON       = 8    # Worlord pool starts here

# ── Game states ───────────────────────────────────────────────────────────────
STATE_TITLE    = "title"
STATE_PLAYING  = "playing"
STATE_PAUSED   = "paused"
STATE_GAMEOVER = "gameover"
STATE_BETWEEN  = "between"   # dungeon transition
STATE_WORLUK   = "worluk"    # Worluk fleeing sequence
STATE_WIZARD   = "wizard"    # Wizard active

# ── Heartbeat ─────────────────────────────────────────────────────────────────
HEARTBEAT_BASE   = 1.4    # seconds between beats (full dungeon)
HEARTBEAT_MIN    = 0.25   # fastest beat at 1 enemy left

# ── Wizard taunts ─────────────────────────────────────────────────────────────
WIZARD_TAUNTS = [
    "I AM THE WIZARD OF WOR!",
    "FIND ME IF YOU CAN...",
    "MY WORRIORS, WHERE ARE YOU?",
    "GET THE WORLUK!",
    "YOU CANNOT ESCAPE!",
    "FOOLS... ALL OF YOU!",
    "THE DUNGEON IS MINE!",
]
