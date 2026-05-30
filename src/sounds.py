"""sounds.py — Procedural audio synthesis using numpy + pygame."""
import pygame
import numpy as np
import math


_RATE = 44100
_initialized = False
_sounds: dict = {}


def init():
    global _initialized
    if _initialized:
        return
    pygame.mixer.pre_init(_RATE, -16, 1, 512)
    pygame.mixer.init()
    _initialized = True
    _build_sounds()


def _tone(freq: float, duration: float, volume: float = 0.4,
          wave: str = "square", fade_out: float = 0.0) -> pygame.mixer.Sound:
    n = int(_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if wave == "square":
        arr = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "sawtooth":
        arr = 2 * (t * freq - np.floor(t * freq + 0.5))
    elif wave == "sine":
        arr = np.sin(2 * np.pi * freq * t)
    elif wave == "noise":
        arr = np.random.uniform(-1, 1, n)
    else:
        arr = np.sin(2 * np.pi * freq * t)

    if fade_out > 0:
        fade_n = int(_RATE * fade_out)
        fade_n = min(fade_n, n)
        arr[-fade_n:] *= np.linspace(1, 0, fade_n)

    # Envelope
    env = np.ones(n)
    attack = int(_RATE * 0.005)
    env[:attack] = np.linspace(0, 1, attack)
    env[-min(int(_RATE*0.01), n):] *= np.linspace(1, 0, min(int(_RATE*0.01), n))
    arr = arr * env * volume

    arr16 = np.int16(arr * 32767)
    return pygame.sndarray.make_sound(arr16)


def _chirp(f0: float, f1: float, duration: float, volume: float = 0.4) -> pygame.mixer.Sound:
    n = int(_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    arr = np.sin(2 * np.pi * np.cumsum(freq) / _RATE)
    env = np.ones(n)
    env[-int(n*0.2):] *= np.linspace(1, 0, int(n*0.2))
    arr = arr * env * volume
    return pygame.sndarray.make_sound(np.int16(arr * 32767))


def _build_sounds():
    global _sounds
    _sounds["shot_p1"]     = _chirp(800, 200, 0.12, 0.35)
    _sounds["shot_p2"]     = _chirp(600, 180, 0.12, 0.35)
    _sounds["shot_enemy"]  = _chirp(400, 100, 0.14, 0.25)
    _sounds["death_player"]= _chirp(500, 60, 0.5, 0.5)
    _sounds["death_enemy"] = _chirp(300, 50, 0.18, 0.4)
    _sounds["worluk"]      = _chirp(1200, 200, 0.4, 0.45)
    _sounds["wizard_zap"]  = _chirp(2000, 100, 0.3, 0.5)
    _sounds["bonus_life"]  = _chirp(440, 880, 0.4, 0.5)
    _sounds["dungeon_clear"]= _chirp(330, 660, 0.6, 0.45)
    _sounds["heartbeat"]   = _tone(80, 0.08, 0.3, "sine")
    _sounds["warp"]        = _chirp(600, 1200, 0.2, 0.3)


def play(name: str, volume: float = 1.0):
    if not _initialized:
        return
    s = _sounds.get(name)
    if s:
        s.set_volume(volume)
        s.play()


class Heartbeat:
    def __init__(self):
        self._timer = 0.0
        self.interval = 1.4

    def update(self, dt: float, enemies_alive: int, enemies_total: int):
        from src.constants import HEARTBEAT_BASE, HEARTBEAT_MIN
        frac = max(0, enemies_alive - 1) / max(1, enemies_total)
        self.interval = HEARTBEAT_MIN + frac * (HEARTBEAT_BASE - HEARTBEAT_MIN)

        self._timer -= dt
        if self._timer <= 0:
            self._timer = self.interval
            play("heartbeat", 0.4)

    @property
    def bpm(self) -> float:
        return 60.0 / max(0.01, self.interval)
