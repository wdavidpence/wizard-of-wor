# Wizard of Wor Arcade Refactor Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Refactor the existing single-file Wizard of Wor to be more faithful to the 1981 Midway arcade original by adding 2-player co-op, attract mode, color-cycling walls, CRT effect, in-canvas HUD, and other arcade-accurate features.

**Architecture:** Single-file rewrite (keep index.html approach for portability). All new features added inline. Phaser 3.90.0 from CDN. No new dependencies.

**Tech Stack:** HTML5, Phaser 3.90.0, Web Audio API, localStorage

---

## Refactoring Strategy

The current file is 1491 lines. We will expand to ~2000-2200 lines. The structure stays:
1. Constants & config
2. Pixel art drawing engine
3. Audio engine
4. Maze generation
5. Game Scene class (all game logic)
6. Phaser config & init
7. Start/Game Over screens (now in-canvas)

Key architectural decisions:
- Player 2 is a separate game object tracked alongside Player 1
- Attract mode uses Phaser tweens for flashing title
- Color cycling tracked via `level` variable, applied to wall drawing
- CRT effect via fixed-size overlay canvas with scanline pattern
- HUD drawn directly in Phaser (no HTML overlay for score/lives)
- High scores stored in localStorage, shown in attract mode

---

## Task 1: 2-Player Co-Op System

**Objective:** Add Player 2 with alternating lives, drop-in mechanic, and on-screen indicator.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — Game Scene

**Changes:**
- Add `player2` object alongside `player` (same entity structure)
- Add `p1Lives = 3, p2Lives = 3` tracking
- When Player 1 dies: Player 2 respawns at start position, Player 1 enters backup state
- When Player 2 dies (while P1 alive): P1 drops to P2's position, P2 enters backup
- HUD shows both players' lives with labels
- Color P1 blue, P2 red to distinguish

**Step 1: Add player2 state and HUD display**

Add to GameScene `create()`:
```javascript
this.player2 = null; this.p2Lives = 3;
```

Update `updateHUD()` to show both:
```javascript
// Draw P1 lives (blue) and P2 lives (red) on screen
// Update existing HUD text elements
```

**Step 2: Modify killPlayer for alternating**

Current `killPlayer()` needs to become `killCurrentPlayer()`:
- Track which player died
- If Player 1 dies: Player 2 continues from spawn point, Player 1 gets backup
- If Player 2 dies (and P1 is alive): P1 takes over, P2 gets backup
- If both have 0 lives: Game Over

**Step 3: Spawn second player at start**

In `startLevel()`, after spawning Player 1, also spawn Player 2 at the reserve position.

**Verification:** Run the game. Each player has 3 lives. Killing P1 drops P2. Killing P2 drops P1. Game ends only when both out of lives.

---

## Task 2: Attract Mode with Flashing Title

**Objective:** Replace static HTML start screen with Phaser-based attract mode matching the arcade cabinet.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — Game Scene + Phaser config

**Changes:**
- Add `attractMode = true` to game state
- Flashing "WIZARD OF WOR" title with color cycling
- Scrolling instructions
- "INSERT COIN / TAP TO START" blink
- High score display from localStorage
- In attract mode, show randomly moving Burwors as decoration
- On player input (key press or touch), transition to game

**Step 1: Draw attract screen in Phaser**

Replace the `#startScreen` HTML overlay with an in-canvas attract mode. Add to `create()`:
```javascript
this.attractMode = true;
// Draw title with flashing
this.attractTitle = this.add.text(MAZE_W/2, MAZE_H*0.3, 'WIZARD OF WOR', {
  fontFamily: 'Press Start 2P', fontSize: '22px', color: '#ff00ff'
}).setOrigin(0.5);
// Instructions
this.attractInstr = this.add.text(MAZE_W/2, MAZE_H*0.55, 'PLAYER 1: ARROW KEYS + SPACE\nPLAYER 2: NUMPAD + NUM0\n\nCROSS HAIRS — P1   DIAMONDS — P2', {
  fontFamily: 'Press Start 2P', fontSize: '8px', color: '#00ff88', align: 'center', lineSpacing: 6
}).setOrigin(0.5);
this.attractTap = this.add.text(MAZE_W/2, MAZE_H*0.85, 'TAP OR PRESS ANY KEY', {
  fontFamily: 'Press Start 2P', fontSize: '10px', color: '#ffea00'
}).setOrigin(0.5);
```

**Step 2: Attract mode update loop**

In `update()`, if `attractMode`:
- Flash title (toggle alpha with tween)
- Show high score
- On any input, call `this.startAttractGame()`

**Step 3: Remove HTML overlays**

Replace `#startScreen` and `#gameOverScreen` divs with simpler HTML. Game over becomes in-canvas.

**Verification:** Game starts with flashing title, instructions, and high score. Tap/keypress starts game.

---

## Task 3: Color-Cycling Walls

**Objective:** Walls change color each level like the original arcade game (5-color cycle).

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — `drawMaze()` method

**Step 1: Define color palette**

Add near constants:
```javascript
const WALL_COLORS = [
  0x2244cc, // blue
  0x22cc44, // green
  0xcc2222, // red
  0xcccc22, // yellow
  0x22cccc  // cyan
];
```

**Step 2: Apply to drawMaze**

In `drawMaze()`, change wall fill colors:
```javascript
const wallColor = WALL_COLORS[this.level % 5];
g.fillStyle(wallColor, 1);
g.fillRect(c * CELL, r * CELL, CELL, CELL);
// Inner highlight lighter
const lighter = Phaser.Display.Color.GetColor(
  Phaser.Display.Color.RedToNumber(wallColor) + 0x222222
);
// Just use the base color for now, simplified
```

**Verification:** Each new level has a different wall color cycling through the 5 colors.

---

## Task 4: CRT Scanline Effect

**Objective:** Add scanline overlay for authentic CRT arcade feel.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — CSS + a Phaser overlay

**Step 1: Add scanline overlay to Phaser**

In `create()`, after maze is drawn:
```javascript
this.crtGfx = this.add.graphics();
this.crtGfx.setDepth(50).setScrollFactor(0);
// Draw scanlines at a fixed rate
this.showCRT = true;
```

In `update()`:
```javascript
if (this.showCRT) this.drawCRT();
```

```javascript
drawCRT() {
  const g = this.crtGfx;
  g.clear();
  for (let y = 0; y < GAME_H; y += 3) {
    g.fillStyle(0x000000, 0.15);
    g.fillRect(0, y, GAME_W, 1);
  }
}
```

**Step 2: Add slight vignette**

In `drawCRT()`, add corner darkening:
```javascript
// Simple vignette with radial gradient approximation
g.fillStyle(0x000000, 0.2);
g.fillCircle(0, 0, 100); // top-left corner darkening
g.fillCircle(GAME_W, 0, 100); // top-right
g.fillCircle(0, GAME_H, 100); // bottom-left
g.fillCircle(GAME_W, GAME_H, 100); // bottom-right
```

**Verification:** Scanlines visible over the game, slight vignette at corners.

---

## Task 5: In-Canvas HUD

**Objective:** Move score/lives/level display from HTML overlay to Phaser canvas.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — Game Scene

**Step 1: Draw HUD in create**

Replace `updateHUD()` with full canvas drawing:
```javascript
this.hudGfx = this.add.graphics();

updateHUD() {
  this.hudGfx.clear();
  const g = this.hudGfx;
  // Top bar background
  g.fillStyle(0x111133, 0.8);
  g.fillRect(0, 0, GAME_W, 36);
  // Score
  g.fillStyle(0xffea00, 1);
  this.add.text(10, 8, 'SCORE: ' + this.score.toString().padStart(7, '0'), {
    fontFamily: 'Press Start 2P', fontSize: '10px', color: '#ffea00'
  });
  // Player 2 label
  this.add.text(300, 8, 'P2: ' + this.p2Lives, {
    fontFamily: 'Press Start 2P', fontSize: '10px', color: '#ff4444'
  });
  // Level
  this.add.text(GAME_W - 160, 8, 'LEVEL: ' + this.level, {
    fontFamily: 'Press Start 2P', fontSize: '10px', color: '#00ff88'
  });
  // Player 1 lives
  this.add.text(500, 8, 'P1: ' + this.p1Lives, {
    fontFamily: 'Press Start 2P', fontSize: '10px', color: '#4488ff'
  });
}
```

**Verification:** Score, lives for both players, and level displayed at top of canvas.

---

## Task 6: Wizard Taunt Text

**Objective:** Show Wizard taunts as on-screen text, matching arcade behavior.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — Game Scene

**Step 1: Add taunt text list**

Add to the teleport block in `updateEnemyAI`:
```javascript
const taunts = [
  "WARRIOR... THE WIZARD OF WOR!",
  "YOU CANNOT DEFEAT ME!",
  "I AM THE WIZARD OF WOR!",
  "YOUR WORST NIGHTMARE!",
  "HUNT ME IF YOU DARE!",
  "THE WIZARD IS WATCHING!",
  "YOU WILL NEVER CATCH ME!"
];
// Pick random, show for 2 seconds
const tauntText = this.add.text(MAZE_W/2, 50, taunts[Math.floor(Math.random()*taunts.length)], {
  fontFamily: 'Press Start 2P', fontSize: '10px', color: '#ff00ff',
  stroke: '#000000', strokeThickness: 3
}).setOrigin(0.5).setDepth(200);
this.tweens.add({
  targets: tauntText, alpha: 0, duration: 2000,
  onComplete: () => tauntText.destroy()
});
```

**Verification:** When Wizard teleports, text appears on screen with his taunt.

---

## Task 7: Score Counting Animation

**Objective:** Kill points count up rapidly (100 → score) like the arcade original.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — `handleBulletCollisions()`

**Step 1: Replace instant scoring with animation**

In `handleBulletCollisions()`, replace:
```javascript
this.score += pointsAwarded;
this.updateHUD();
```

With animated counter:
```javascript
const startScore = this.score;
this.score += pointsAwarded;
this.updateHUD();
// Animate score counting up
const countAnim = this.add.text(10, 8, 'SCORE: ' + startScore.toString().padStart(7, '0'), {
  fontFamily: 'Press Start 2P', fontSize: '10px', color: '#ffea00'
}).setDepth(200);
this.tweens.add({
  targets: countAnim,
  text: 'SCORE: ' + (startScore + pointsAwarded).toString().padStart(7, '0'),
  duration: 500,
  onUpdate: () => { /* update live */ },
  onComplete: () => countAnim.destroy()
});
```

Actually simpler approach: just keep instant score but add a floating "+N" that animates up, which we already have. The arcade original's counting-up is subtle. Let's keep it simple with the existing floating points display.

**Verification:** Killing enemies shows floating +N text that animates up and fades.

---

## Task 8: Warp Tunnel Animation & Better Visuals

**Objective:** Animate warp tunnels (pulsing purple) and improve visual polish.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — `drawMaze()` and `update()`

**Step 1: Pulsing warp tunnel**

In `drawMaze()`, animate tunnel colors:
```javascript
const tunnelPulse = 0.5 + 0.5 * Math.sin(time / 300);
g.fillStyle(Phaser.Display.Color.GetColor(
  128 + 127 * tunnelPulse | 0, 0, 128 + 127 * tunnelPulse | 0
), 1);
g.fillRect(0, r * CELL, CELL, CELL);
```

Actually simpler - just tint the existing tunnel fill:
```javascript
const pulse = 0.6 + 0.4 * Math.sin(time / 400);
g.fillStyle(0xff00ff, pulse);
```

**Step 2: Player glow effect**

Add subtle glow around player:
```javascript
// In update(), if player alive:
if (this.player && this.player.alive) {
  if (!this.playerGlow || !this.playerGlow.active) {
    this.playerGlow = this.add.circle(this.player.x, this.player.y, CELL * 0.55, 0x4488ff, 0.25);
    this.entityLayer.add(this.playerGlow);
    this.playerGlow.setDepth(this.player.depth - 1);
  } else {
    this.playerGlow.x = this.player.x;
    this.playerGlow.y = this.player.y;
    this.playerGlow.setAlpha(0.2 + 0.1 * Math.sin(time / 400));
  }
}
```

**Verification:** Warp tunnels pulse purple, player has subtle blue glow.

---

## Task 9: High Score Persistence

**Objective:** Save and display high scores using localStorage.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — start screen

**Step 1: Add high score storage**

Helper functions:
```javascript
function getHighScores() {
  try { return JSON.parse(localStorage.getItem('wor_scores') || '[]'); } catch(e) { return []; }
}
function saveScore(score) {
  const scores = getHighScores();
  scores.push({ score, date: new Date().toISOString(), level: currentLevel });
  scores.sort((a, b) => b.score - a.score);
  localStorage.setItem('wor_scores', JSON.stringify(scores.slice(0, 5)));
}
```

**Step 2: Show in attract mode**

In attract mode update, display top 3 scores.

**Verification:** High scores persist across browser sessions.

---

## Task 10: Game Over Animation (In-Canvas)

**Objective:** Replace HTML overlay Game Over with Phaser-based screen.

**Files:**
- Modify: `/Users/davidpence/wizard-of-wor/index.html` — `gameOver()`

**Step 1: Draw game over in canvas**

Replace `gameOver()`:
```javascript
gameOver() {
  this.state = 'gameover';
  this.showCRT = false; // Remove CRT for clean game over

  const overlay = this.add.container(0, 0).setDepth(200);
  overlay.setSize(MAZE_W, GAME_H);
  const bg = this.add.rectangle(MAZE_W/2, MAZE_H/2, MAZE_W, GAME_H, 0x000000, 0.95);
  overlay.add(bg);

  const title = this.add.text(MAZE_W/2, MAZE_H*0.3, 'GAME OVER', {
    fontFamily: 'Press Start 2P', fontSize: '28px', color: '#ff0000'
  }).setOrigin(0.5);
  overlay.add(title);

  const scoreTxt = this.add.text(MAZE_W/2, MAZE_H*0.5, 'FINAL SCORE: ' + this.score, {
    fontFamily: 'Press Start 2P', fontSize: '14px', color: '#ffea00'
  }).setOrigin(0.5);
  overlay.add(scoreTxt);

  const levelTxt = this.add.text(MAZE_W/2, MAZE_H*0.6, 'REACHED LEVEL: ' + this.level, {
    fontFamily: 'Press Start 2P', fontSize: '10px', color: '#00ff88'
  }).setOrigin(0.5);
  overlay.add(levelTxt);

  // Save high score
  saveScore(this.score, this.level);
  const hs = getHighScores()[0];
  if (hs && hs.score === this.score) {
    this.add.text(MAZE_W/2, MAZE_H*0.7, 'NEW HIGH SCORE!', {
      fontFamily: 'Press Start 2P', fontSize: '12px', color: '#ff00ff'
    }).setOrigin(0.5).setDepth(201);
  }

  const restart = this.add.text(MAZE_W/2, MAZE_H*0.85, 'TAP OR PRESS ANY KEY', {
    fontFamily: 'Press Start 2P', fontSize: '10px', color: '#ffea00'
  }).setOrigin(0.5);
  overlay.add(restart);

  // Blink animation
  this.tweens.add({
    targets: restart, alpha: 0, duration: 600,
    yoyo: true, repeat: -1
  });
}
```

**Verification:** Game over shows in-canvas with animated text.

---

## Summary of File Changes

All changes are in `/Users/davidpence/wizard-of-wor/index.html`:

1. Add player2 state, p1Lives/p2Lives tracking, alternating death logic
2. Add attract mode with flashing title, instructions, high scores
3. Add WALL_COLORS array and cycle in drawMaze()
4. Add CRT scanline overlay graphics
5. Move HUD to in-canvas display (score, lives both players, level)
6. Add Wizard taunt text display
7. Keep existing floating points (sufficient for scoring)
8. Add warp tunnel pulse animation, player glow
9. Add localStorage high score functions
10. Replace Game Over HTML overlay with Phaser container

---

## Execution Order

1. Task 5 (HUD) first — easiest, establishes canvas-based UI
2. Task 3 (Color walls) — pure visual change
3. Task 4 (CRT) — pure visual, no game logic
4. Task 1 (2-player) — core gameplay change
5. Task 2 (Attract mode) — depends on HUD being in canvas
6. Task 6 (Taunts) — minor polish
7. Task 8 (Warp + glow) — minor polish
8. Task 7 (Score animation) — minor polish
9. Task 9 (High scores) — depends on attract mode
10. Task 10 (Game Over) — depends on HUD being in canvas
