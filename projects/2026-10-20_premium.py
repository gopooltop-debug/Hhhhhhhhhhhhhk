"""Реклама кошелька из кожи крокодила по референсу «iPhone 17 Pro — 3D Animation» (Naimorphic):
тёмная «студийная» картинка, свет проходит по фактуре, резкие склейки под бит со смазом и наездами,
ускорения/замедления, пролёты камеры, крупные титры с трекингом, удар на кульминации, финальный титр.

Запуск: python3 projects/2026-10-20_premium.py IMG_7542.MOV [папка_вывода]
Исходник: IMG_7542.MOV (Google Диск «Видео реклама премиум»), 1080×1920, 59,94 к/с, 15 мин.
Музыка синтезируется здесь же (120 BPM, ля минор) — без чужих треков.
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402  (шрифты, запись звука, −14 LUFS)

SRC = sys.argv[1] if len(sys.argv) > 1 else "IMG_7542.MOV"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
NAME = "2026-10-20_премиум_v1"
W, H, FPS, SFPS = 1080, 1920, 30, 60
SR = 48000
BEAT = 0.5   # 120 BPM


# ------------------------------------------------------------------ таймлайн
# src — начало в исходнике; ramp — [(длительность в ролике, скорость)];
# z/r/pan — зум, поворот (град), сдвиг (px) от начала к концу плана; enter — переход на план.
class Shot:
    def __init__(self, src, ramp, z=(1.0, 1.0), r=(0.0, 0.0), pan=((0, 0), (0, 0)),
                 focus=(0.5, 0.5), enter="cut", ease="io", sweep=None):
        self.src, self.ramp, self.z, self.r, self.pan = src, ramp, z, r, pan
        self.focus, self.enter, self.ease, self.sweep = focus, enter, ease, sweep
        self.dur = sum(d for d, _ in ramp)

    def src_time(self, t):
        s, acc = self.src, 0.0
        for d, sp in self.ramp:
            if t <= acc + d:
                return s + (t - acc) * sp, sp
            s += d * sp
            acc += d
        return s, self.ramp[-1][1]

    def src_end(self):
        return self.src_time(self.dur)[0]


SHOTS = [
    # 0,0 — из темноты: кошелёк на камне, свет проходит по коже
    Shot(104.0, [(2.0, 1.0)], z=(1.10, 1.22), r=(-2.5, 0), focus=(0.45, 0.42), sweep=(0.35, 1.75)),
    # 2,0 — пролёт к фактуре, ускорение ×3
    Shot(108.4, [(1.0, 3.0)], z=(1.05, 1.15), enter="zoom"),
    # 3,0 — макро фактуры, медленный наезд с поворотом
    Shot(113.0, [(2.0, 1.0)], z=(1.20, 1.42), r=(0, 4), focus=(0.55, 0.55), enter="spin", sweep=(3.15, 4.6)),
    # 5,0 — ремесло: линейка ложится на кожу
    Shot(383.85, [(1.0, 2.0)], z=(1.10, 1.18), enter="whip"),
    # 6,0 — нож вдоль линейки
    Shot(392.9, [(0.5, 2.0)], z=(1.25, 1.32), focus=(0.4, 0.55), enter="cut"),
    Shot(407.5, [(0.5, 2.0)], z=(1.20, 1.28), focus=(0.4, 0.5), enter="cut"),
    # 7,0 — пробойник
    Shot(490.0, [(1.0, 2.0)], z=(1.25, 1.35), focus=(0.4, 0.45), enter="zoom"),
    Shot(553.0, [(1.0, 2.0)], z=(1.30, 1.22), focus=(0.35, 0.45), enter="cut"),
    # 9,0 — перчатки поворачивают готовый кошелёк
    Shot(628.1, [(1.0, 1.5)], z=(1.05, 1.15), enter="spin"),
    # 10,0 — пролёты камеры вокруг кошелька
    Shot(845.6, [(1.5, 2.0)], z=(1.05, 1.12), enter="whip"),
    Shot(899.0, [(1.5, 2.0)], z=(1.08, 1.0), enter="zoom", sweep=(11.6, 12.9)),
    # 13,0 — кульминация: пачка денег падает на кошелёк, замедление ×0,3
    Shot(765.95, [(0.6, 1.0), (1.4, 0.3), (0.5, 1.6)], z=(1.06, 1.16), focus=(0.4, 0.5), enter="flash"),
    # 15,5 — финал: кошелёк низко над камнем, титр
    Shot(879.0, [(3.5, 0.7)], z=(1.22, 1.06), r=(1.5, 0), focus=(0.5, 0.6), enter="zoom", ease="out",
         sweep=(16.0, 17.8)),
]
STARTS = np.cumsum([0] + [s.dur for s in SHOTS])
TOTAL = float(STARTS[-1])
LANDING = STARTS[11] + 0.6 + (766.75 - 766.55) / 0.3   # пачка ложится на кошелёк
SHAKES = [(STARTS[6] + 0.25, 10), (STARTS[7], 8), (STARTS[11], 14), (LANDING, 22), (STARTS[12], 8)]
FADE_IN = (0.0, 1.0)
FADE_OUT = (TOTAL - 0.7, TOTAL)


class Title:
    def __init__(self, t0, t1, lines, y):
        self.t0, self.t1, self.lines, self.y = t0, t1, lines, y   # lines: [(text, role, size)]


TITLES = [
    Title(3.25, 4.85, [("натуральная", "inter500", 46), ("КОЖА КРОКОДИЛА", "mont800", 84)], 900),
    Title(5.15, 8.85, [("РУЧНАЯ РАБОТА", "mont800", 84), ("от раскроя до последнего шва", "inter500", 40)], 300),
    Title(16.0, TOTAL, [("PREMIUM", "mont900", 150), ("кошелёк из кожи крокодила", "inter500", 46)], 360),
]


# ------------------------------------------------------------------ утилиты
def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_io(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp01(x)) ** 3


def lerp(a, b, k):
    return a + (b - a) * k


class Reader:
    """Кадры плана по порядку (60 к/с), с небольшим буфером назад."""

    def __init__(self, shot):
        span = shot.src_end() - shot.src + 0.3
        self.p = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{shot.src:.3f}", "-t", f"{span:.3f}", "-i", SRC,
             "-vf", f"fps={SFPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
            stdout=subprocess.PIPE)
        self.buf, self.base = [], 0

    def get(self, i):
        while self.base + len(self.buf) <= i:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                return self.buf[-1]
            self.buf.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
            if len(self.buf) > 12:
                self.buf.pop(0)
                self.base += 1
        return self.buf[max(0, i - self.base)]

    def close(self):
        self.p.stdout.close()
        self.p.kill()


def src_frame(reader, local_src, speed):
    """Кадр в момент local_src (с от начала плана); на ускорении — смаз (затвор 180°)."""
    i = local_src * SFPS
    n = max(1, int(round(speed)))
    if n == 1:
        return reader.get(int(round(i))).astype(np.float32)
    acc = np.zeros((H, W, 3), np.float32)
    for k in range(n):
        acc += reader.get(int(i) + k)
    return acc / n


# ---------------------------------------------------------------- цвет
def grade_lut():
    x = np.arange(256, dtype=np.float32) / 255
    s = x - 0.035                                 # глубже чёрный
    s = np.clip(s / 0.93, 0, 1)
    s = s + 0.22 * s * (1 - s) * (2 * s - 1) * 2  # S-кривая
    s = np.clip(s, 0, 1)
    b = np.clip(s * 1.0 + 0.020 * (1 - s) ** 3, 0, 1)   # холодные тени
    g = s
    r = np.clip(s * 1.02 - 0.012 * (1 - s) ** 3, 0, 1)  # тёплые света
    return np.stack([b, g, r], 1) * 255


LUT = grade_lut()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = 1 - 0.55 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.48) / (H * 0.60)) ** 2, 0, 1) ** 1.3
VIG = VIG[..., None].astype(np.float32)


def grade(f):
    f = np.clip(f, 0, 255)
    idx = f.astype(np.uint8)
    out = np.empty_like(f)
    for c in range(3):
        out[..., c] = LUT[idx[..., c], c]
    gray = out.mean(2, keepdims=True)
    out = gray + (out - gray) * 0.80               # гранит спокойнее, кожа не «синеет»
    return out * VIG


def sweep_mask(k, angle=-35):
    """Полоса света, проходящая по диагонали (k: 0→1)."""
    a = math.radians(angle)
    d = (xx - W / 2) * math.cos(a) + (yy - H / 2) * math.sin(a)
    span = (W * abs(math.cos(a)) + H * abs(math.sin(a))) / 2 + 300
    c = lerp(-span, span, k)
    return np.exp(-((d - c) / 170) ** 2)[..., None]


# ---------------------------------------------------------------- геометрия и переходы
def affine(scale, rot, cx, cy, dx, dy):
    # центр зума не даёт кадру уйти за край (иначе снизу/сбоку видно отражение)
    cx = min(max(cx, W / (2 * scale)), W - W / (2 * scale))
    cy = min(max(cy, H / (2 * scale)), H - H / (2 * scale))
    M = cv2.getRotationMatrix2D((cx, cy), rot, scale)
    M[0, 2] += W / 2 - cx + dx
    M[1, 2] += H / 2 - cy + dy
    return M


def warp(f, M):
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def zoom_blur(f, amt, steps=7):
    if amt < 0.004:
        return f
    acc = np.zeros_like(f)
    for k in range(steps):
        s = 1 + amt * k / (steps - 1)
        acc += warp(f, affine(s, 0, W / 2, H / 2, 0, 0))
    return acc / steps


def dir_blur(f, length, vertical=False):
    length = int(length)
    if length < 3:
        return f
    small = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    k = max(3, length // 4)
    kern = np.zeros((k, k), np.float32)
    if vertical:
        kern[:, k // 2] = 1 / k
    else:
        kern[k // 2, :] = 1 / k
    small = cv2.filter2D(small, -1, kern)
    blurred = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    mix = min(1.0, length / 60)
    return f * (1 - mix) + blurred * mix


def transition_state(t):
    """Состояние склейки для момента t: тип, сторона (-1 — уходящий план, +1 — входящий), сила 0..1."""
    for i in range(1, len(SHOTS)):
        c = STARTS[i]
        kind = SHOTS[i].enter
        if kind == "cut":
            continue
        dt = t - c
        if -0.12 <= dt < 0:
            return kind, -1, 1 - (-dt) / 0.12
        if 0 <= dt < 0.22:
            return kind, 1, 1 - dt / 0.22
    return None, 0, 0.0


def shake_at(t):
    dx = dy = 0.0
    for t0, amp in SHAKES:
        dt = t - t0
        if 0 <= dt < 0.4:
            a = amp * math.exp(-dt * 9)
            dx += a * math.sin(dt * 95)
            dy += a * math.cos(dt * 77)
    return dx, dy


# ---------------------------------------------------------------- титры
def title_layer(t):
    layer = None
    for ti in TITLES:
        if not (ti.t0 <= t < ti.t1 + 0.35):
            continue
        k_in = ease_out((t - ti.t0) / 0.6)
        k_out = 1 - ease_io((t - ti.t1) / 0.35) if t > ti.t1 else 1.0
        alpha = k_in * k_out
        if alpha <= 0.01:
            continue
        if layer is None:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        y = ti.y
        for li, (text, role, size) in enumerate(ti.lines):
            delay = 0.12 * li
            kl = ease_out((t - ti.t0 - delay) / 0.6)
            spacing = int(size * lerp(0.42, 0.10, kl))   # трекинг: буквы сходятся
            img = m.text_image(text, role, size, (245, 242, 236), spacing)
            if img.width > W - 120:
                img = img.resize((W - 120, int(img.height * (W - 120) / img.width)), Image.LANCZOS)
            blur = lerp(10, 0, kl) + (1 - k_out) * 8
            if blur > 0.3:
                img = img.filter(ImageFilter.GaussianBlur(blur))
            a = np.array(img)
            a[..., 3] = (a[..., 3] * alpha * clamp01(kl * 1.3)).astype(np.uint8)
            img = Image.fromarray(a)
            # мягкая тень для читаемости
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sh.putalpha(img.getchannel("A").point(lambda v: int(v * 0.55)))
            sh = sh.filter(ImageFilter.GaussianBlur(14))
            x0 = (W - img.width) // 2
            yy0 = int(y - img.height / 2 + lerp(18, 0, kl))
            layer.alpha_composite(sh, (x0, yy0 + 4))
            layer.alpha_composite(img, (x0, yy0))
            y += int(size * 0.62 + ti.lines[min(li + 1, len(ti.lines) - 1)][2] * 0.75)
    return layer


def overlay(frame, layer):
    if layer is None:
        return frame
    a = np.asarray(layer, np.float32)
    al = a[..., 3:4] / 255
    rgb = a[..., [2, 1, 0]]
    return frame * (1 - al) + rgb * al


# ---------------------------------------------------------------- рендер видео
def render_video(path):
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    n_total = int(round(TOTAL * FPS))
    for si, sh in enumerate(SHOTS):
        rd = Reader(sh)
        f0, f1 = int(round(STARTS[si] * FPS)), int(round(STARTS[si + 1] * FPS))
        for fi in range(f0, min(f1, n_total)):
            t = fi / FPS
            lt = t - STARTS[si]
            u = lt / sh.dur
            src_t, speed = sh.src_time(lt)
            f = src_frame(rd, src_t - sh.src, speed)
            ke = ease_out(u) if sh.ease == "out" else ease_io(u)
            scale = lerp(*sh.z, ke)
            rot = lerp(*sh.r, ke)
            dx = lerp(sh.pan[0][0], sh.pan[1][0], ke)
            dy = lerp(sh.pan[0][1], sh.pan[1][1], ke)
            kind, side, amt = transition_state(t)
            if kind == "zoom":
                scale *= 1 + 0.10 * amt if side > 0 else 1 + 0.06 * amt
            elif kind == "spin":
                rot += (-14 * amt) if side > 0 else (10 * amt)
                scale *= 1 + 0.08 * amt
            elif kind == "whip":
                dx += (220 * amt) if side > 0 else (-180 * amt)
                scale *= 1 + 0.08 * amt
            elif kind == "flash":
                scale *= 1 + 0.12 * amt if side > 0 else 1.0
            sx, sy = shake_at(t)
            M = affine(scale, rot, W * sh.focus[0], H * sh.focus[1], dx + sx, dy + sy)
            f = warp(f, M)
            if kind == "zoom":
                f = zoom_blur(f, 0.09 * amt)
            elif kind == "spin":
                f = zoom_blur(f, 0.05 * amt)
                f = dir_blur(f, 70 * amt, vertical=True)
            elif kind == "whip":
                f = dir_blur(f, 200 * amt)
            f = grade(f)
            if sh.sweep and sh.sweep[0] <= t < sh.sweep[1]:
                k = (t - sh.sweep[0]) / (sh.sweep[1] - sh.sweep[0])
                msk = sweep_mask(ease_io(k)) * 0.30 * math.sin(math.pi * k)
                f = f + (255 - f) * msk
            if kind == "flash" and side > 0:
                f = f + (255 - f) * 0.55 * amt ** 2
            if kind in ("zoom", "spin", "whip") and side > 0:
                f = f + (255 - f) * 0.10 * amt ** 2
            if abs(t - LANDING) < 0.12:
                f = f + (255 - f) * 0.18 * (1 - abs(t - LANDING) / 0.12)
            expo = 1.0
            if t < FADE_IN[1]:
                expo = ease_io((t - FADE_IN[0]) / (FADE_IN[1] - FADE_IN[0])) ** 1.4
            if t > FADE_OUT[0]:
                expo *= 1 - ease_io((t - FADE_OUT[0]) / (FADE_OUT[1] - FADE_OUT[0]))
            if si == len(SHOTS) - 1:
                expo *= lerp(1.0, 0.82, ease_io((lt - 0.4) / 1.2))   # финал темнее под титр
            f = f * expo
            f = overlay(f, title_layer(t))
            enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        rd.close()
        print(f"план {si + 1}/{len(SHOTS)} готов", flush=True)
    enc.stdin.close()
    enc.wait()


# ---------------------------------------------------------------- музыка и звук
N = int(TOTAL * SR) + SR
rng = np.random.default_rng(7)


def at(buf, t, x, g=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += x * g


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 42 + 110 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 6.5)
    x += 0.25 * rng.standard_normal(n) * np.exp(-t * 180)
    return np.tanh(x * 1.6) * 0.9


def clap():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    b, a = signal.butter(2, [900 / (SR / 2), 5000 / (SR / 2)], "band")
    x = signal.lfilter(b, a, noise)
    e = np.exp(-t * 22)
    for d in (0.0, 0.011, 0.022):
        e += 0.6 * np.exp(-np.maximum(t - d, 0) * 90) * (t >= d)
    return x * e * 0.5


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    b, a = signal.butter(2, 7000 / (SR / 2), "high")
    x = signal.lfilter(b, a, rng.standard_normal(n))
    return x * np.exp(-t * (14 if open_ else 70)) * 0.22


def boom(dur=3.0, f0=55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 1.2 * np.exp(-t * 7))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3)
    b, a = signal.butter(2, 900 / (SR / 2), "low")
    nz = signal.lfilter(b, a, rng.standard_normal(n)) * np.exp(-t * 4) * 0.6
    return np.tanh((x + nz) * 1.4)


def whoosh(dur=0.45, rise=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 512
    for i in range(0, n, seg):
        k = i / n if rise else 1 - i / n
        fc = 300 + 5000 * k ** 2
        b, a = signal.butter(2, [fc / (SR / 2), min(0.99, fc * 1.8 / (SR / 2))], "band")
        out[i:i + seg] = signal.lfilter(b, a, x[i:i + seg])
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** (2 if rise else 1)
    if rise:
        e *= (t / dur) ** 1.5
    return out * e * 0.9


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = t / dur
    f = 200 * 2 ** (k * 3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (whoosh(dur, True) * 0.8 + tone) * k ** 2


def tick():
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 3100 * t) * np.exp(-t * 120) + 0.4 * rng.standard_normal(n) * np.exp(-t * 300)
    return x * 0.35


def note(freq, dur, kind="pad"):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        f = freq * 2 ** (det / 12)
        x += signal.sawtooth(2 * np.pi * f * t + rng.uniform(0, 6))
    b, a = signal.butter(2, (900 if kind == "pad" else 2400) / (SR / 2), "low")
    x = signal.lfilter(b, a, x) / 3
    a_t = 0.6 if kind == "pad" else 0.005
    e = np.minimum(1, t / a_t) * np.minimum(1, (dur - t) / 0.5).clip(0, 1)
    return x * e


def bell(freq, dur=3.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * d)
            for a, r, d in ((1, 1, 1.2), (0.5, 2.76, 2.5), (0.3, 5.4, 4), (0.2, 2.0, 1.6)))
    return x * 0.25


def reverb(x, sec=2.2, wet=0.25):
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 6.9 / sec)
    b, a = signal.butter(1, 5000 / (SR / 2), "low")
    ir = signal.lfilter(b, a, ir)
    ir /= np.sqrt((ir ** 2).sum())
    y = signal.fftconvolve(x, ir)[: len(x)]
    return x * (1 - wet) + y * wet * 3


def hz(nn):
    return 440 * 2 ** ((nn - 69) / 12)


def build_music():
    music = np.zeros(N)
    drums = np.zeros(N)
    sfx = np.zeros(N)
    climax = STARTS[11]
    finale = STARTS[12]
    # гармония: Am | F | Dm | E | (кульминация) Am | финал Am(add9)
    chords = [(0, 4, [45, 48, 52, 57]), (4, 8, [41, 45, 48, 53]), (8, 11, [38, 45, 50, 53]),
              (11, climax, [40, 44, 47, 52]), (climax, finale, [33, 45, 52]),
              (finale, TOTAL + 0.5, [45, 52, 57, 59, 60])]
    for t0, t1, notes in chords:
        for nn in notes:
            at(music, t0, note(hz(nn), t1 - t0 + 0.6), 0.10)
    # бас: восьмые с «выдохом» от бочки, 3–13 с
    roots = [(3, 4, 33), (4, 8, 29), (8, 11, 26), (11, 12.5, 28)]
    for t0, t1, r in roots:
        t = t0
        while t < t1 - 1e-6:
            x = note(hz(r + 12), 0.22, "bass") + 0.6 * np.sin(2 * np.pi * hz(r) * np.arange(int(0.22 * SR)) / SR)
            at(music, t, x * env(len(x), 0.004, 0.12), 0.32)
            t += BEAT / 2
    # барабаны: 5–12,5 с полный бит, 3–5 только хэты
    t = 3.0
    while t < 12.5 - 1e-6:
        beat_i = round((t - 3.0) / (BEAT / 2))
        if t >= 5.0 and beat_i % 2 == 0:
            at(drums, t, kick(), 0.9)
        if t >= 5.0 and beat_i % 4 == 2:
            at(drums, t, clap(), 0.7)
        at(drums, t, hat(open_=(beat_i % 4 == 3 and t >= 5.0)), 0.8 if beat_i % 2 else 0.5)
        t += BEAT / 2
    # кульминация: подъём, тишина, удар; удар на падении пачки
    at(sfx, 11.0, riser(climax - 11.0 - 0.08), 0.7)
    at(drums, climax, boom(3.0, 50), 0.95)
    at(sfx, climax, whoosh(0.5, False), 0.5)
    at(drums, LANDING, kick(), 1.0)
    at(drums, LANDING, boom(2.0, 62), 0.6)
    at(sfx, LANDING - 0.35, whoosh(0.4, True), 0.6)
    # финал: удар-логотип и колокол
    at(drums, finale, boom(3.5, 45), 0.8)
    for i, nn in enumerate((69, 76, 81)):
        at(music, finale + 0.5 + 0.12 * i, bell(hz(nn)), 0.35)
    # вжухи на переходах, тики на ремесле
    for i, sh in enumerate(SHOTS[1:], 1):
        if sh.enter in ("zoom", "spin", "whip") and STARTS[i] not in (climax, finale):
            at(sfx, STARTS[i] - 0.3, whoosh(0.42, True), 0.55)
        if sh.enter == "cut":
            at(sfx, STARTS[i], tick(), 0.6)
    at(sfx, STARTS[6] + 0.25, tick(), 0.9)
    at(sfx, STARTS[7] + 0.05, tick(), 0.9)
    at(sfx, 0.0, whoosh(1.4, False) * 0.5, 0.6)
    # сайдчейн: музыка проседает под бочку
    duck = np.ones(N)
    t = 5.0
    while t < 12.5:
        i = int(t * SR)
        n = int(0.22 * SR)
        duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.55 * np.exp(-np.arange(n) / SR * 14))
        t += BEAT
    music = reverb(music * duck, 2.6, 0.35)
    mix = music + drums + reverb(sfx, 1.6, 0.25)
    # общий фейд в конце
    tt = np.arange(N) / SR
    mix *= np.clip((TOTAL - tt) / 0.9, 0, 1)
    mix *= np.clip(tt / 0.15, 0, 1)
    mix = mix[: int(TOTAL * SR)]
    mix = np.tanh(mix * 1.1) / 1.1
    return (mix / (np.abs(mix).max() + 1e-9) * 0.89).astype(np.float32)


def main():
    work = os.path.join(OUT_DIR, "_work")
    os.makedirs(work, exist_ok=True)
    v = os.path.join(work, NAME + "_video.mp4")
    a_raw = os.path.join(work, NAME + "_music_raw.wav")
    a = os.path.join(work, NAME + "_music.wav")
    if "--audio-only" not in sys.argv:
        render_video(v)
    m.write_wav(a_raw, build_music())
    m.loudnorm(a_raw, a)
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    m.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", out])
    print(out, f"{TOTAL:.2f} с")


if __name__ == "__main__":
    main()
