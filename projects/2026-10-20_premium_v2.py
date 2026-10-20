"""«Премиум» v2 — по референсу «iPhone 17 Pro — 3D Animation #blender» (Naimorphic Studio), покадрово:

  0,0–1,2  чёрный, кошелёк едва виден в центре; на 0,65 «включается свет» — тёплые блики по чешуе
  1,2–3,65 резкий наезд вплотную: медленный облёт края, тёплый свет идёт по коже, уход в чёрный
  3,7–7,45 крупно фактура, медленный поворот (как блок камер в референсе), свет гаснет
  7,5–11,25 темнота, свет поднимается снизу вверх и проявляет кошелёк, снова гаснет
  11,28–16,4 общий план «на камнях», вступает бит; маленькая подпись сверху и в углу
  16,43–17,53 логотип на чёрном, тишина

Картинка — почти монохром, низкий ключ, всё в замедлении ×0,5–0,6 со стабилизацией (vidstab),
чтобы движение было плавным, как у 3D. Музыка синтезирована (102 BPM, ре минор) — без чужих треков.

Запуск: python3 projects/2026-10-20_premium_v2.py IMG_7542.MOV [папка_вывода]
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402  (шрифты, запись звука, −14 LUFS)

SRC = sys.argv[1] if len(sys.argv) > 1 else "IMG_7542.MOV"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
NAME = "2026-10-20_премиум_v2"
WORK = os.path.join(OUT_DIR, "_work", "premium_v2")
W, H, FPS, SFPS = 1080, 1920, 30, 60
SR = 48000
AMBER = np.array([0.22, 0.50, 1.0], np.float32)   # BGR: тёплый «экранный» свет из референса


def clamp01(x):
    return float(min(1.0, max(0.0, x)))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def ramp(t, t0, t1):
    return smooth((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)


# ------------------------------------------------------------------ планы
class Shot:
    """src — начало в исходнике, speed — скорость, t0/t1 — место в ролике.
    z/r — зум и поворот от начала к концу, focus — центр кадра в исходнике,
    spot — пятно света в исходнике (cx, cy, rx, ry), floor — освещённость вне пятна.
    light(t) — общая яркость, warm(t) — сила тёплых бликов, reveal(t) — граница света снизу (1 → 0)."""

    def __init__(self, t0, t1, src, speed, z, r, focus, spot, floor, light, warm=None, reveal=None,
                 smash=False, gain=1.0):
        self.t0, self.t1, self.src, self.speed = t0, t1, src, speed
        self.gain = gain
        self.z, self.r, self.focus, self.spot, self.floor = z, r, focus, spot, floor
        self.light, self.warm, self.reveal, self.smash = light, warm, reveal, smash

    @property
    def span(self):
        return (self.t1 - self.t0) * self.speed + 0.4


SHOTS = [
    Shot(0.00, 1.20, 82.0, 0.5, z=(0.60, 0.66), r=(0, 0), focus=(0.48, 0.47),
         spot=(0.48, 0.47, 0.42, 0.20), floor=0.0, gain=1.6,
         light=lambda t: lerp(0.10, 0.20, ramp(t, 0, 0.6)) + 0.55 * ramp(t, 0.62, 0.85),
         warm=lambda t: 1.8 * ramp(t, 0.62, 0.78)),
    Shot(1.20, 3.65, 900.7, 0.5, z=(1.40, 1.26), r=(-5, 3), focus=(0.62, 0.45),
         spot=(0.62, 0.42, 0.42, 0.40), floor=0.18,
         light=lambda t: 1.0 - ramp(t, 3.35, 3.65),
         warm=lambda t: 3.2 - 1.0 * ramp(t, 1.2, 3.4), smash=True, gain=2.1),
    Shot(3.70, 7.45, 113.0, 0.5, z=(1.30, 1.46), r=(0, 9), focus=(0.58, 0.58),
         spot=(0.6, 0.55, 0.50, 0.42), floor=0.12,
         light=lambda t: ramp(t, 3.70, 4.30) * (1 - ramp(t, 6.70, 7.42)),
         warm=lambda t: 0.5 + 0.9 * math.exp(-((t - 5.3) / 0.7) ** 2), gain=2.0),
    Shot(7.50, 11.25, 616.0, 0.5, z=(1.75, 1.95), r=(0, -3), focus=(0.5, 0.56),
         spot=(0.5, 0.56, 0.45, 0.25), floor=0.10, gain=2.2,
         light=lambda t: 1 - ramp(t, 10.75, 11.22),
         reveal=lambda t: lerp(1.25, -0.30, ramp(t, 7.6, 10.2)),
         warm=lambda t: 0.4 + 1.0 * math.exp(-((t - 9.6) / 0.6) ** 2)),
    Shot(11.28, 16.40, 874.0, 0.6, z=(1.04, 1.12), r=(2, 0), focus=(0.55, 0.55),
         spot=(0.58, 0.55, 0.50, 0.38), floor=0.35, gain=1.35,
         light=lambda t: lerp(0.8, 1.0, ramp(t, 11.28, 11.6)),
         warm=lambda t: 0.25 + 0.9 * math.exp(-((t - 15.0) / 0.55) ** 2)),
]
TOTAL = 17.53
LOGO_T = 16.43
DROP = 11.28


# ------------------------------------------------------------------ исходники со стабилизацией
def prepare(sh):
    os.makedirs(WORK, exist_ok=True)
    out = os.path.join(WORK, f"clip_{sh.src:.2f}.mp4")
    if os.path.exists(out):
        return out
    trf = out[:-4] + ".trf"
    common = ["-ss", f"{sh.src:.3f}", "-t", f"{sh.span:.3f}", "-i", SRC]
    m.run(["ffmpeg", "-v", "error", "-y", *common, "-vf",
           f"vidstabdetect=shakiness=6:accuracy=15:result={trf}", "-f", "null", "-"])
    m.run(["ffmpeg", "-v", "error", "-y", *common, "-vf",
           f"vidstabtransform=input={trf}:smoothing=45:optzoom=1:interpol=bicubic,fps={SFPS}",
           "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-an", out])
    return out


class Reader:
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo",
                                   "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        self.buf, self.base = [], 0

    def get(self, i):
        i = max(0, i)
        while self.base + len(self.buf) <= i:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                return self.buf[-1]
            self.buf.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
            if len(self.buf) > 6:
                self.buf.pop(0)
                self.base += 1
        return self.buf[max(0, i - self.base)]

    def at(self, t):
        """Кадр в момент t (с от начала клипа) — смесь двух соседних кадров (замедление без рывков)."""
        x = t * SFPS
        i = int(x)
        k = x - i
        a = self.get(i).astype(np.float32)
        if k < 0.05:
            return a
        return a * (1 - k) + self.get(i + 1).astype(np.float32) * k

    def close(self):
        self.p.stdout.close()
        self.p.kill()


# ------------------------------------------------------------------ свет и цвет
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
YN, XN = YY / H, XX / W


def look(f, sh, t):
    """Низкий ключ: монохром, фактура кожи, гранит в серый, пятно света, тёплые блики на чешуе."""
    f = f / 255.0
    y = f[..., 2] * 0.299 + f[..., 1] * 0.587 + f[..., 0] * 0.114
    bl = cv2.GaussianBlur(y, (0, 0), 18)
    y2 = np.clip(y + 1.1 * (y - bl), 0, 1)
    hi = 0.32
    y3 = np.where(y2 < hi, y2 * 1.15, hi * 1.15 + (y2 - hi) * 0.38) * sh.gain
    y3 = np.where(y3 < 0.7, y3, 0.7 + (1 - np.exp(-(y3 - 0.7) * 3)) * 0.3)   # мягкий потолок
    cx, cy, rx, ry = sh.spot
    d = ((XN - cx) / rx) ** 2 + ((YN - cy) / ry) ** 2
    mask = sh.floor + (1 - sh.floor) * np.exp(-d * 1.4)
    if sh.reveal:
        lvl = sh.reveal(t)   # граница света: всё ниже неё освещено
        mask = mask * np.clip((YN - lvl) / 0.35 + 0.5, 0, 1) ** 1.5
    y4 = np.clip(y3 * mask, 0, 1) ** 1.12
    out = np.stack([y4 * 1.02, y4, y4 * 0.98], -1)
    if sh.warm:
        w = sh.warm(t)
        if w > 0.01:
            ridge = np.clip((y - cv2.GaussianBlur(y, (0, 0), 4)) * 9, 0, 1)
            dark = np.clip((0.30 - cv2.GaussianBlur(y, (0, 0), 25)) / 0.12, 0, 1)
            out = out + (ridge * dark * mask * w * 1.6)[..., None] * AMBER * 0.55
    return out * sh.light(t)


def place(img, sh, t):
    u = smooth((t - sh.t0) / (sh.t1 - sh.t0))
    z = lerp(*sh.z, u)
    if sh.smash:   # резкий наезд в начале плана
        z *= 1 + 0.18 * (1 - smooth((t - sh.t0) / 0.35))
    rot = lerp(*sh.r, u)
    cx, cy = W * sh.focus[0], H * sh.focus[1]
    if z >= 1:
        cx = min(max(cx, W / (2 * z)), W - W / (2 * z))
        cy = min(max(cy, H / (2 * z)), H - H / (2 * z))
    M = cv2.getRotationMatrix2D((cx, cy), rot, z)
    M[0, 2] += W / 2 - cx
    M[1, 2] += H / 2 - cy
    border = cv2.BORDER_REFLECT if z >= 1 else cv2.BORDER_CONSTANT
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border, borderValue=0)


def film(out):
    # мягкое свечение светов и чуть зерна — «рендер», а не телефон
    glow = cv2.GaussianBlur(np.clip(out - 0.45, 0, 1), (0, 0), 22)
    out = out + glow * 0.35
    vign = 1 - 0.35 * np.clip(((XN - 0.5) / 0.75) ** 2 + ((YN - 0.5) / 0.8) ** 2, 0, 1)
    return out * vign[..., None]


# ------------------------------------------------------------------ подписи и логотип
GREY = (205, 205, 205)


def diamond(size, width=3, color=GREY):
    img = Image.new("RGBA", (size * 2 + 8, size * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size + 4
    pts = [(c, c - size), (c + size, c), (c, c + size), (c - size, c), (c, c - size)]
    d.line(pts, fill=color + (255,), width=width, joint="curve")
    s2 = int(size * 0.45)
    d.polygon([(c, c - s2), (c + s2, c), (c, c + s2), (c - s2, c)], fill=color + (255,))
    return img


def text_layer(t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    used = False
    # подпись сверху, как «iPhone» в референсе: знак + слово, появляется из размытия
    k = ramp(t, 13.8, 14.6) * (1 - ramp(t, 16.30, 16.40))
    if k > 0.01:
        used = True
        word = m.text_image("PREMIUM", "mont600", 40, GREY, spacing=int(lerp(22, 12, k)))
        icon = diamond(15, 2)
        row = Image.new("RGBA", (icon.width + 18 + word.width, max(icon.height, word.height)), (0, 0, 0, 0))
        row.alpha_composite(icon, (0, (row.height - icon.height) // 2))
        row.alpha_composite(word, (icon.width + 18, (row.height - word.height) // 2))
        row = row.filter(ImageFilter.GaussianBlur(lerp(6, 0, k)))
        a = np.array(row)
        a[..., 3] = (a[..., 3] * 0.72 * k).astype(np.uint8)
        row = Image.fromarray(a)
        layer.alpha_composite(row, ((W - row.width) // 2, 300))
    # мелкая подпись слева, как «K. Naim» в референсе
    k2 = ramp(t, 11.6, 12.0) * (1 - ramp(t, 13.3, 13.7))
    if k2 > 0.01:
        used = True
        for i, line in enumerate(("кожа крокодила", "ручная работа")):
            im = m.text_image(line, "inter500", 24, (190, 190, 190))
            a = np.array(im)
            a[..., 3] = (a[..., 3] * 0.6 * k2).astype(np.uint8)
            layer.alpha_composite(Image.fromarray(a), (72, 1180 + i * 34))
    # логотип на чёрном
    k3 = ramp(t, LOGO_T, LOGO_T + 0.15)
    if t >= LOGO_T:
        used = True
        icon = diamond(34, 3)
        word = m.text_image("PREMIUM", "mont600", 26, GREY, spacing=10)
        a1, a2 = np.array(icon), np.array(word)
        a1[..., 3] = (a1[..., 3] * k3).astype(np.uint8)
        a2[..., 3] = (a2[..., 3] * k3 * 0.85).astype(np.uint8)
        layer.alpha_composite(Image.fromarray(a1), ((W - icon.width) // 2, 900))
        layer.alpha_composite(Image.fromarray(a2), ((W - word.width) // 2, 900 + icon.height + 16))
    return layer if used else None


def overlay(frame, layer):
    if layer is None:
        return frame
    a = np.asarray(layer, np.float32) / 255
    al = a[..., 3:4]
    return frame * (1 - al) + a[..., [2, 1, 0]] * al


# ------------------------------------------------------------------ видео
def render_video(path):
    clips = [prepare(sh) for sh in SHOTS]
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    readers = {}
    black = np.zeros((H, W, 3), np.float32)
    for fi in range(int(round(TOTAL * FPS))):
        t = fi / FPS
        out = black
        for si, sh in enumerate(SHOTS):
            if sh.t0 <= t < sh.t1:
                if si not in readers:
                    readers[si] = Reader(clips[si])
                f = readers[si].at((t - sh.t0) * sh.speed)
                f = place(f, sh, t)
                out = film(look(f, sh, t))
                break
        out = overlay(out, text_layer(t))
        enc.stdin.write(np.clip(out * 255 if out is not black else out, 0, 255).astype(np.uint8).tobytes())
        if fi % 60 == 0:
            print(f"{t:5.1f} с", flush=True)
    for r in readers.values():
        r.close()
    enc.stdin.close()
    enc.wait()


# ------------------------------------------------------------------ музыка (102 BPM, ре минор)
BPM = 102
BEAT = 60 / BPM
BAR = 4 * BEAT
GRID0 = DROP - 4 * BAR          # сильная доля такта приходится на смену плана 11,28
N = int((TOTAL + 1) * SR)
rng = np.random.default_rng(11)


def hz(nn):
    return 440 * 2 ** ((nn - 69) / 12)


def add(buf, t, x, g=1.0):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    x = x[: max(0, len(buf) - i)]
    buf[i:i + len(x)] += x * g


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def pad(freq, dur, bright=900):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(signal.sawtooth(2 * np.pi * freq * 2 ** (d / 1200) * t + rng.uniform(0, 6)) for d in (-9, 0, 8))
    x = lp(x / 3, bright)
    e = np.minimum(1, t / 0.9) * np.clip((dur - t) / 0.8, 0, 1)
    return x * e


def pluck(freq, dur=0.9, bright=2600):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.35 * signal.sawtooth(2 * np.pi * freq * t, 0.5) \
        + 0.15 * np.sin(2 * np.pi * freq * 2 * t)
    x = lp(x, bright) * np.exp(-t * 5.5) * np.minimum(1, t / 0.003)
    return x


def sub(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t) * np.minimum(1, t / 0.01) * np.clip((dur - t) / 0.05, 0, 1)


def kick():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    x += 0.15 * lp(rng.standard_normal(n), 3000) * np.exp(-t * 120)
    return np.tanh(x * 1.5)


def snare():
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    b, a = signal.butter(2, [1200 / (SR / 2), 7000 / (SR / 2)], "band")
    x = signal.lfilter(b, a, rng.standard_normal(n)) * np.exp(-t * 16)
    x += 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    return x * 0.6


def hat(dec=70):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 8000) * np.exp(-t * dec) * 0.25


def boom(dur=3.0, f0=48):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-t * 6))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    x += 0.5 * lp(rng.standard_normal(n), 700) * np.exp(-t * 5)
    return np.tanh(x * 1.3)


def swell(dur, up=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = t / dur if up else 1 - t / dur
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 480
    zi = None
    for i in range(0, n, seg):
        fc = 250 + 6000 * (k[i] ** 2)
        b, a = signal.butter(2, [fc / (SR / 2), min(0.98, fc * 1.6 / (SR / 2))], "band")
        y, zi = signal.lfilter(b, a, x[i:i + seg], zi=zi if zi is not None else signal.lfilter_zi(b, a) * 0)
        out[i:i + seg] = y
    return out * (k ** 2.2) * 1.4


def shimmer(dur=2.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * hz(nn) * t + rng.uniform(0, 6)) for nn in (86, 89, 93, 98))
    return x * np.minimum(1, t / 0.05) * np.exp(-t * 2.2) * 0.15


def hum(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 55 * t) + 0.4 * np.sin(2 * np.pi * 110 * t) + 0.15 * signal.sawtooth(2 * np.pi * 220 * t)
    return lp(x, 600) * np.minimum(1, t / 0.08) * np.clip((dur - t) / 0.5, 0, 1)


def reverb(x, sec=2.5, wet=0.3):
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = lp(rng.standard_normal(n), 6000) * np.exp(-t * 6.9 / sec)
    ir /= np.sqrt((ir ** 2).sum())
    return x * (1 - wet) + signal.fftconvolve(x, ir)[: len(x)] * wet * 3


def delay(x, d, fb=0.35, mix=0.3):
    y = x.copy()
    k = int(d * SR)
    for i in range(1, 5):
        y[k * i:] += x[: len(x) - k * i] * (fb ** i) * mix / 0.35
    return y


# аккорды по тактам: Dm9 | B♭maj7 | Fadd9 | C(sus) ; ноты MIDI
CHORDS = [[50, 53, 57, 60, 64], [46, 50, 53, 57, 60], [41, 45, 48, 52, 55], [48, 52, 55, 57, 62]]
ROOTS = [38, 34, 41, 36]


def build_music():
    music = np.zeros(N)
    plk = np.zeros(N)
    drums = np.zeros(N)
    sfx = np.zeros(N)
    # пэд с самого начала (из тишины)
    bar_i = -1
    t = GRID0 - BAR
    while t < LOGO_T:
        ch = CHORDS[bar_i % 4]
        dur = min(BAR + 0.9, LOGO_T + 0.25 - t)
        if dur > 0.2:
            for nn in ch:
                add(music, max(t, 0), pad(hz(nn), dur, 1100 if t >= DROP else 800)[int(max(0, -t) * SR):], 0.075)
        # арпеджио восьмыми (с 1,9 с), после дропа ярче
        if t >= GRID0 - 1e-6:
            order = [0, 2, 3, 4, 3, 2, 1, 2]
            for k in range(8):
                tt = t + k * BEAT / 2
                if tt >= LOGO_T - 0.05:
                    break
                nn = ch[order[k]] + 12
                add(plk, tt, pluck(hz(nn), 0.8, 3600 if t >= DROP else 3000), 0.17)
        # бас после дропа
        if t >= DROP - 1e-6:
            r = ROOTS[bar_i % 4]
            for k in range(8):
                tt = t + k * BEAT / 2
                if tt >= LOGO_T - 0.05:
                    break
                x = sub(hz(r), BEAT / 2 * 0.9) + 0.25 * lp(signal.sawtooth(2 * np.pi * hz(r + 12) * np.arange(int(BEAT / 2 * 0.9 * SR)) / SR), 900)
                add(music, tt, x * np.exp(-np.arange(len(x)) / SR * 3), 0.30)
        bar_i += 1
        t += BAR
    # бит после дропа
    t = DROP
    k = 0
    while t < LOGO_T - 0.05:
        if k % 2 == 0:
            add(drums, t, kick(), 0.85)
        if k % 4 == 2:
            add(drums, t, snare(), 0.55)
        add(drums, t, hat(90 if k % 2 == 0 else 40), 0.6)
        add(drums, t + BEAT / 4, hat(110), 0.25)
        t += BEAT / 2
        k += 1
    # звук под картинку
    add(sfx, 0.62, hum(0.9), 0.20)          # «включился свет»
    add(sfx, 0.62, shimmer(1.6), 0.9)
    add(sfx, 1.20 - 0.55, swell(0.55), 0.35)  # наезд
    add(drums, 1.20, boom(2.2, 52), 0.55)
    add(sfx, 3.70 - 0.45, swell(0.45), 0.22)
    add(drums, 3.70, boom(1.8, 60), 0.30)
    add(sfx, 7.50 - 0.5, swell(0.5), 0.18)
    add(sfx, 7.65, shimmer(2.0), 0.6)
    add(sfx, 9.0, swell(DROP - 9.0 - 0.06), 0.5)   # подъём к дропу
    add(drums, DROP, boom(2.6, 46), 0.75)
    add(sfx, 13.8, shimmer(1.8), 0.6)               # подпись
    # ритм «дышит» под бочку
    duck = np.ones(N)
    t = DROP
    while t < LOGO_T:
        i = int(t * SR)
        n = int(0.25 * SR)
        duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.45 * np.exp(-np.arange(n) / SR * 12))
        t += BEAT
    plk = delay(plk, BEAT * 0.75, 0.38, 0.35)
    music = reverb(music + plk, 3.0, 0.38) * duck
    mix = music + drums + reverb(sfx, 2.0, 0.3)
    # как в референсе: на логотипе музыка обрывается, остаётся короткий хвост
    tt = np.arange(N) / SR
    mix *= np.where(tt < LOGO_T, 1.0, np.exp(-(tt - LOGO_T) * 9))
    mix *= np.clip(tt / 0.05, 0, 1)
    mix = mix[: int(TOTAL * SR)]
    mix = np.tanh(mix * 1.2) / 1.2
    return (mix / (np.abs(mix).max() + 1e-9) * 0.89).astype(np.float32)


def main():
    os.makedirs(WORK, exist_ok=True)
    v = os.path.join(WORK, NAME + "_video.mp4")
    a_raw = os.path.join(WORK, NAME + "_music_raw.wav")
    a = os.path.join(WORK, NAME + "_music.wav")
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
