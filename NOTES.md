# Modern Wizard of Wor — Agent Memory

## Architecture Decisions
- Engine: pygame-ce 2.5.7, Python 3.11
- Resolution: 1280×800 (16:9 modern), scales to 720p
- Maze: 22×14 grid (doubled from original 11×6 for HD, each cell = 48px)
- Rendering: per-cell wall tiles drawn procedurally, no external art assets needed
- Colors: neon-on-black aesthetic (cyberpunk/modern take on the original)

## Iteration Log
| # | Date | Summary | Score |
|---|------|---------|-------|
| 0 | init | Project scaffolded | - |

## Known Bugs
(none yet)

## Current Task Queue
See TASKS.json

## Design Principles
- One shot on screen per player (original rule, keep it)
- Radar bottom-bar shows all enemies including invisible ones
- Enemy invisibility: Garwor fades out, Thorwor fully invisible
- Heartbeat SFX tempo increases as enemies die
- Wizard taunts via text overlays (no Votrax, but animated speech bubbles)
- Double-score dungeon after Worluk kill
- Friendly fire in 2P mode: 1000pts
- Bonus life before Arena (Dungeon 4)
