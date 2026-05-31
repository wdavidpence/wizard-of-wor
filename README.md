# Wizard of WOR — Modern Edition

A full pygame-ce recreation of the classic 1981 arcade shooter **Wizard of WOR**, rebuilt with a neon cyberpunk aesthetic.

## Features

- **6 enemy types**: Burwor, Garwor (invisible), Thorwor (radar-only), Worluk (flees to warp), Wizard of Wor (teleporting boss), Worlord (dungeon miniboss)
- **3 dungeon variants**: Standard (procedurally generated from mirrored templates), Arena (dungeon 4), Pit (dungeon 13, no interior walls)
- **Warp tunnels** — run through the side portals to appear on the opposite side
- **Full 4-dungeon progression** with spawn sequencing, Worluk chase, and Wizard boss
- **Hit-freeze, screenshake, flash effects** — classic arcade juice
- **Neon particle explosions** on kills and wall impacts
- **Procedural audio** — 11 synthesized sound effects (shots, deaths, warp, heartbeat, bonus, dungeon clear)
- **HUD** with live scores, lives, dungeon type labels, and enemy count radar
- **2-player support** with independent controls and friendly fire

## Controls

### Player 1
- **WASD** — Move
- **SPACE** — Shoot

### Player 2
- **Arrow Keys** — Move
- **ENTER** — Shoot

**ESC** — Return to title screen

## Requirements

- Python 3.11+
- `pygame-ce` 2.5+
- `numpy`

## Installation

```bash
pip install pygame-ce numpy
cd wizard-of-wor
python main.py
```

## Smoke Tests

Run the headless smoke test suite:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_game -v
```

All 6 tests pass: 600-frame stability, kills, scoring, particles, Worlord spawn, auto-respawn.

## Architecture

```
src/
  constants.py    — All game parameters, colors, grid dimensions
  maze.py         — Dungeon generation from mirrored templates, wall collision, warp detection
  player.py       — Movement, shooting, wall/warp collision, invulnerability
  enemy.py        — Burwor, Garwor, Thorwor, Worluk, Worlord, WizardOfWor
  bullet.py       — Laser bolts with trails, wall-explode particles, warp passthrough
  game.py         — State machine, dungeon management, spawn sequencer, collision
  hud.py          — Scores, lives, messages, dungeon type labels
  radar.py        — Full entity radar with type-specific colors
  particles.py    — Explosion particle system
  sounds.py       — Procedural audio synthesis (numpy + pygame)
main.py           — Entry point, event loop, key bindings
```

## Development

The game uses a grid-based movement system (48px cells, 22×14 playfield) with cell-anchored positioning to prevent drift. Enemies use directional AI with grid-snapping. All collision uses AABB hitboxes sized to match enemy 28×28 hitboxes.

## History

Built with Hermes Agent over 50 overnight iterations, then manually fixed and verified. All modules in `src/` with comprehensive smoke tests in `tests/`.

---

Wizard of WOR™ is a trademark of Cinematronics. This is a fan tribute built from scratch with no licensed assets.
