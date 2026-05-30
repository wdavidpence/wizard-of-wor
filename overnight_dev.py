#!/usr/bin/env python3
"""
overnight_dev.py — The AI game development orchestrator.

Architecture:
  - Runs up to MAX_ITERATIONS improvement cycles
  - Each cycle: Architect → Coder → Reviewer → Tester pipeline
  - All agents use local Qwen via OpenAI-compatible endpoint
  - Context window is managed by keeping each agent call focused
  - Progress is saved after every iteration (git commit)
  - Headless smoke test after every change
  - NOTES.md and TASKS.json are the persistent memory layer
"""
import os
import sys
import json
import subprocess
import time
import datetime
import traceback
import shutil
import tempfile
from pathlib import Path

from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
QWEN_BASE  = "http://host.docker.internal:8000/v1"
QWEN_KEY   = "a1b2c3d4"
QWEN_MODEL = "Qwen3.6-35B-A3B-MLX-8bit"
PROJECT    = Path("/root/wizard_of_wor")
LOG_DIR    = PROJECT / "logs"
ITER_DIR   = PROJECT / "iterations"
MAX_ITER   = 50
SMOKE_TIMEOUT = 20   # seconds for headless test

client = OpenAI(base_url=QWEN_BASE, api_key=QWEN_KEY)


# ── Logging ───────────────────────────────────────────────────────────────────

log_file = LOG_DIR / f"overnight_{datetime.datetime.now():%Y%m%d_%H%M%S}.log"
LOG_DIR.mkdir(exist_ok=True)

def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")


# ── File helpers ──────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def read_notes() -> str:
    return read_file(PROJECT / "NOTES.md")

def read_tasks() -> list:
    try:
        return json.loads(read_file(PROJECT / "TASKS.json"))
    except Exception:
        return []

def write_tasks(tasks: list):
    write_file(PROJECT / "TASKS.json", json.dumps(tasks, indent=2))

def read_src_file(name: str) -> str:
    return read_file(PROJECT / "src" / name)

def write_src_file(name: str, content: str):
    write_file(PROJECT / "src" / name, content)

def list_src_files() -> list[str]:
    return [f.name for f in (PROJECT / "src").glob("*.py")]


# ── Agent calls ──────────────────────────────────────────────────────────────

def call_agent(system: str, user: str, max_tokens: int = 4096,
               temp: float = 0.3) -> str:
    """Call Qwen with a system + user prompt. Returns the response text."""
    try:
        resp = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        log(f"  [AGENT ERROR] {e}")
        return ""


# ── Agent roles ───────────────────────────────────────────────────────────────

ARCHITECT_SYS = """You are the Lead Architect for a modern Python/pygame remake of 
"Wizard of Wor" (1981 Midway arcade game). You own the technical roadmap.

Game context:
- pygame-ce, 1280x800, 60fps, neon-cyberpunk aesthetic
- 22×14 grid maze, 5 enemy types (Burwor/Garwor/Thorwor/Worluk/Wizard)
- Original mechanics: single-shot-per-player, radar bar, invisible enemies, warp tunnels
- Multi-agent team: you plan, a Coder implements, a Reviewer checks quality, a Tester verifies

Your job: Given the current task list and known bugs, decide the SINGLE highest-value 
task to do in this iteration. Return JSON only:
{
  "task_id": <int>,
  "task_desc": "<description>",
  "target_file": "<src/filename.py>",
  "approach": "<2-3 sentence technical plan>",
  "expected_quality_gain": "<what improves>"
}"""

CODER_SYS = """You are the Lead Coder on a Python/pygame game. You write complete, 
working Python code for a specific file.

Rules:
- Output ONLY the complete new file content — no markdown fences, no explanation
- Keep all existing functionality working — never break what already works  
- Write clean, commented code
- Use pygame-ce APIs correctly
- Every class/function should have a docstring
- The file must be syntactically valid Python 3.11"""

REVIEWER_SYS = """You are a Code Reviewer for a Python/pygame game codebase.
You review a proposed file change for:
1. Correctness (will it work? any logic bugs?)
2. Integration (does it break other modules?)
3. Performance (any obvious bottlenecks?)
4. Game feel (does this improve the actual game experience?)

Be concise. Return JSON:
{
  "approve": true/false,
  "score": 1-10,
  "issues": ["<issue1>", ...],
  "suggestion": "<one key improvement if any>"
}"""

TESTER_SYS = """You are the QA agent for a Python/pygame game. 
You analyze headless test output and error logs to identify bugs.
Return JSON:
{
  "passed": true/false,
  "errors": ["<error>", ...],
  "warnings": ["<warning>", ...],
  "next_fix": "<most important thing to fix>"
}"""


# ── Smoke test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> tuple[bool, str]:
    """Run the game headlessly for 5 seconds. Returns (passed, output)."""
    cmd = [
        sys.executable, "-c",
        """
import sys, os
sys.path.insert(0, '/root/wizard_of_wor')
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 800))
from src.game import Game
import src.sounds as sounds

game = Game(1)
game.start_game()
errors = []
for i in range(300):
    try:
        keys = pygame.key.get_pressed()
        game.update(1/60, keys)
        game.draw(screen)
        pygame.display.flip()
    except Exception as e:
        errors.append(f'Frame {i}: {e}')
        break

if errors:
    print('FAIL:' + '|'.join(errors))
else:
    print(f'PASS: 300 frames. enemies={len(game.enemies)} dungeon={game.dungeon} state={game.state}')
pygame.quit()
"""
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=SMOKE_TIMEOUT, cwd=str(PROJECT))
        out = (r.stdout + r.stderr).strip()
        passed = "PASS:" in out and "FAIL:" not in out and r.returncode == 0
        return passed, out
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: smoke test exceeded 20s"
    except Exception as e:
        return False, f"ERROR: {e}"


# ── Syntax check ──────────────────────────────────────────────────────────────

def syntax_check(code: str) -> tuple[bool, str]:
    import ast
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


# ── Git helpers ───────────────────────────────────────────────────────────────

def git_commit(message: str):
    try:
        subprocess.run(["git", "add", "-A"], cwd=PROJECT, capture_output=True)
        subprocess.run(["git", "commit", "-m", message],
                       cwd=PROJECT, capture_output=True)
    except Exception as e:
        log(f"  [GIT] commit failed: {e}")

def save_iteration_snapshot(n: int):
    """Save a copy of src/ to iterations/iter_N/"""
    dest = ITER_DIR / f"iter_{n:03d}"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(PROJECT / "src", dest)


# ── Main orchestrator loop ────────────────────────────────────────────────────

def update_notes(iteration: int, task_desc: str, score: int, issues: list):
    notes = read_notes()
    entry = f"| {iteration} | {datetime.date.today()} | {task_desc[:50]} | {score}/10 |\n"
    notes = notes.replace("| 0 | init | Project scaffolded | - |\n",
                           "| 0 | init | Project scaffolded | - |\n" + entry, 1)
    if issues:
        bugs_section = "\n".join(f"- {i}" for i in issues[:5])
        # Replace known bugs section
        if "## Known Bugs" in notes:
            lines = notes.split("\n")
            new_lines = []
            in_bugs = False
            for line in lines:
                if line.startswith("## Known Bugs"):
                    in_bugs = True
                    new_lines.append(line)
                    new_lines.append("(updated by agent)")
                    for issue in issues[:5]:
                        new_lines.append(f"- {issue}")
                    continue
                if in_bugs and line.startswith("##"):
                    in_bugs = False
                if not in_bugs:
                    new_lines.append(line)
            notes = "\n".join(new_lines)
    write_file(PROJECT / "NOTES.md", notes)


def orchestrate():
    log("=" * 60)
    log("WIZARD OF WOR — OVERNIGHT AI DEVELOPMENT")
    log(f"Model: {QWEN_MODEL}")
    log(f"Max iterations: {MAX_ITER}")
    log("=" * 60)

    # Initial smoke test
    passed, out = run_smoke_test()
    log(f"Initial smoke test: {'PASS' if passed else 'FAIL'}")
    log(f"  {out[:120]}")
    if not passed:
        log("  FATAL: baseline game broken before we even start!")
        return

    git_commit("iter-0: initial game foundation")
    save_iteration_snapshot(0)

    for iteration in range(1, MAX_ITER + 1):
        log("")
        log(f"━━━ ITERATION {iteration}/{MAX_ITER} ━━━")
        iter_start = time.time()

        tasks = read_tasks()
        notes = read_notes()

        # ── 1. ARCHITECT: pick the next task ─────────────────────────────────
        log("  [Architect] Planning next task...")
        pending = [t for t in tasks if t["status"] == "pending"]
        if not pending:
            log("  All tasks complete! Adding polish tasks...")
            pending = [{
                "id": 999, "status": "pending", "priority": "high",
                "desc": "General polish: improve enemy AI, fix any visual glitches, tune difficulty"
            }]

        tasks_summary = "\n".join(
            f"[{t['id']}] {t['priority'].upper()}: {t['desc']}"
            for t in pending[:8]
        )

        arch_prompt = f"""Current project state:
NOTES:
{notes[:800]}

PENDING TASKS (top {len(pending[:8])}):
{tasks_summary}

Pick the highest-value task to implement next. Consider what will make the 
game most playable and fun right now."""

        arch_resp = call_agent(ARCHITECT_SYS, arch_prompt, max_tokens=600)
        log(f"  [Architect] Response: {arch_resp[:100]}...")

        # Parse architect response
        try:
            arch_data = json.loads(arch_resp)
        except Exception:
            # Try to extract JSON from response
            import re
            m = re.search(r'\{.*\}', arch_resp, re.DOTALL)
            if m:
                try:
                    arch_data = json.loads(m.group())
                except Exception:
                    arch_data = {"task_id": pending[0]["id"],
                                  "task_desc": pending[0]["desc"],
                                  "target_file": "src/game.py",
                                  "approach": "improve game loop and enemy behavior",
                                  "expected_quality_gain": "better gameplay"}
            else:
                arch_data = {"task_id": pending[0]["id"],
                              "task_desc": pending[0]["desc"],
                              "target_file": "src/game.py",
                              "approach": "improve game loop and enemy behavior",
                              "expected_quality_gain": "better gameplay"}

        task_id    = arch_data.get("task_id", pending[0]["id"])
        task_desc  = arch_data.get("task_desc", pending[0]["desc"])
        target_file= arch_data.get("target_file", "src/game.py").replace("src/", "")
        approach   = arch_data.get("approach", "")
        log(f"  [Architect] Task: [{task_id}] {task_desc[:60]}")
        log(f"  [Architect] Target: {target_file}, Approach: {approach[:80]}")

        # ── 2. CODER: implement the task ──────────────────────────────────────
        log("  [Coder] Writing code...")

        current_file = read_src_file(target_file) if (PROJECT / "src" / target_file).exists() else ""
        
        # Build context of related files (keep context lean)
        related_context = ""
        key_files = ["constants.py", "game.py", "maze.py", "enemy.py"]
        for kf in key_files:
            if kf != target_file and (PROJECT / "src" / kf).exists():
                content = read_src_file(kf)
                related_context += f"\n--- {kf} (first 80 lines) ---\n"
                related_context += "\n".join(content.split("\n")[:80]) + "\n"

        coder_prompt = f"""TASK: {task_desc}

APPROACH: {approach}

CURRENT FILE ({target_file}):
{current_file[:3000]}

RELATED MODULES (for integration reference):
{related_context[:2000]}

Write the complete improved {target_file} file. Implement the task fully.
Return ONLY the complete Python file content, no markdown, no explanation."""

        new_code = call_agent(CODER_SYS, coder_prompt, max_tokens=4096, temp=0.2)

        if not new_code or len(new_code) < 100:
            log("  [Coder] Empty/too short response, skipping iteration")
            continue

        # Strip markdown fences if present
        if "```python" in new_code:
            new_code = new_code.split("```python", 1)[1].split("```")[0].strip()
        elif "```" in new_code:
            new_code = new_code.split("```", 1)[1].split("```")[0].strip()

        # Syntax check
        ok, err = syntax_check(new_code)
        if not ok:
            log(f"  [Coder] SYNTAX ERROR: {err}")
            log("  Skipping this iteration due to syntax error")
            continue

        log(f"  [Coder] Generated {len(new_code)} chars, syntax OK")

        # ── 3. REVIEWER: check the code ───────────────────────────────────────
        log("  [Reviewer] Reviewing code...")

        review_prompt = f"""Review this proposed change to {target_file}:

TASK BEING IMPLEMENTED: {task_desc}

PROPOSED NEW CODE (first 2000 chars):
{new_code[:2000]}

Does this code correctly implement the task? Any bugs or integration issues?"""

        review_resp = call_agent(REVIEWER_SYS, review_prompt, max_tokens=600)
        log(f"  [Reviewer] Response: {review_resp[:100]}...")

        try:
            review_data = json.loads(review_resp)
        except Exception:
            import re
            m = re.search(r'\{.*\}', review_resp, re.DOTALL)
            review_data = json.loads(m.group()) if m else {"approve": True, "score": 7, "issues": []}

        approved = review_data.get("approve", True)
        score    = review_data.get("score", 7)
        issues   = review_data.get("issues", [])
        log(f"  [Reviewer] Score: {score}/10, Approved: {approved}, Issues: {len(issues)}")

        if not approved and score < 4:
            log("  [Reviewer] REJECTED code — skipping write")
            continue

        # ── 4. Write the file ─────────────────────────────────────────────────
        # Backup original
        backup_path = PROJECT / "src" / f"{target_file}.bak"
        if (PROJECT / "src" / target_file).exists():
            shutil.copy2(PROJECT / "src" / target_file, backup_path)

        write_src_file(target_file, new_code)
        log(f"  Written: {target_file}")

        # ── 5. TESTER: smoke test ─────────────────────────────────────────────
        log("  [Tester] Running headless smoke test...")
        test_passed, test_out = run_smoke_test()
        log(f"  [Tester] {'PASS ✓' if test_passed else 'FAIL ✗'}: {test_out[:100]}")

        if not test_passed:
            # Restore backup
            log("  [Tester] Rolling back...")
            if backup_path.exists():
                shutil.copy2(backup_path, PROJECT / "src" / target_file)
            # Let Tester agent analyze and suggest a fix
            tester_prompt = f"""Smoke test FAILED after writing {target_file}.
Error output:
{test_out[:600]}

What went wrong and what should be fixed?"""
            tester_resp = call_agent(TESTER_SYS, tester_prompt, max_tokens=400)
            log(f"  [Tester] Analysis: {tester_resp[:120]}")
            continue

        # Clean up backup
        if backup_path.exists():
            backup_path.unlink()

        # ── 6. Update task list + notes ───────────────────────────────────────
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "done"
                break
        write_tasks(tasks)
        update_notes(iteration, task_desc, score, issues)

        # ── 7. Git commit ─────────────────────────────────────────────────────
        git_commit(f"iter-{iteration}: [{task_id}] {task_desc[:60]} (score {score}/10)")
        save_iteration_snapshot(iteration)

        elapsed = time.time() - iter_start
        log(f"  ✓ Iteration {iteration} complete in {elapsed:.1f}s")

        # Brief pause between iterations
        time.sleep(2)

    log("")
    log("=" * 60)
    log(f"OVERNIGHT BUILD COMPLETE — {MAX_ITER} iterations")
    log(f"Log: {log_file}")
    log("=" * 60)


if __name__ == "__main__":
    try:
        orchestrate()
    except KeyboardInterrupt:
        log("Interrupted by user")
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())
