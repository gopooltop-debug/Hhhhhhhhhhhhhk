"""Движок монтажа по style/montage-style.md (кадр 1080x1920, 30 к/с).

Проект описывает таймлайн (отрезки исходника, переходы, зумы) и события
графики; движок рендерит видео кадр за кадром и собирает звук.
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 48000
SPF = SR // FPS  # сэмплов звука на кадр
DISSOLVE = 6     # кадров (п. 10)

# Палитра (п. 4)
BLACK = (0x17, 0x16, 0x14)
BROWN = (0x3B, 0x34, 0x2B)
GREEN = (0x37, 0x42, 0x3D)
BORDO = (0x75, 0x40, 0x43)
BEIGE = (0x9A, 0x88, 0x73)
TEXT = (0xF3, 0xEE, 0xE6)
ACCENT = (0xD9, 0xC7, 0xA9)

GRADE = ("eq=contrast=1.07:saturation=0.82:gamma=0.98,"
         "colorbalance=rs=-0.03:gs=0.01:bs=0.02:bm=-0.01:rh=0.03:gh=0.01:bh=-0.03,"
         "curves=all='0/0.035 0.5/0.48 1/0.96'")
VIGNETTE = "vignette=angle=PI/5.5:mode=forward"

VOICE_CHAIN = ("highpass=f=85,afftdn=nr=14:nf=-48:tn=1,"
               "equalizer=f=220:t=q:w=1:g=-2.5,equalizer=f=3200:t=q:w=1:g=2.5,"
               "highshelf=f=9000:g=1.5,deesser=i=0.35,"
               "acompressor=threshold=0.08:ratio=3:attack=6:release=90:makeup=1.6,"
               "alimiter=limit=0.89")

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONTS = {
    "inter500": ["inter-cyrillic-500-normal.ttf", "inter-latin-500-normal.ttf"],
    "inter600": ["inter-cyrillic-600-normal.ttf", "inter-latin-600-normal.ttf"],
    "lora": ["lora-cyrillic-600-italic.ttf", "lora-latin-600-italic.ttf"],
}


# ---------------------------------------------------------------- утилиты

def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


# ---------------------------------------------------------------- текст

_font_cache = {}
_cmap_cache = {}


def _font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(os.path.join(FONT_DIR, path), size)
    return _font_cache[key]


def _cmap(path):
    if path not in _cmap_cache:
        from fontTools.ttLib import TTFont
        _cmap_cache[path] = set(TTFont(os.path.join(FONT_DIR, path)).getBestCmap())
    return _cmap_cache[path]


def _font_for(role, ch):
    files = FONTS[role]
    for f in files:
        if ord(ch) in _cmap(f):
            return f
    return files[-1]


_text_cache = {}


def text_image(text, role, size, color, spacing=0):
    """RGBA-картинка строки с разрядкой; шрифт подбирается по символу
    (кириллический и латинский наборы fontsource лежат в разных файлах)."""
    key = (text, role, size, color, spacing)
    if key in _text_cache:
        return _text_cache[key]
    pad = int(size * 0.6)
    widths = []
    for ch in text:
        f = _font(_font_for(role, ch), size)
        widths.append(f.getlength(ch))
    total = sum(widths) + spacing * max(0, len(text) - 1)
    img = Image.new("RGBA", (int(total) + 2 * pad, int(size * 1.6) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    base = pad + int(size * 1.15)
    for ch, w in zip(text, widths):
        f = _font(_font_for(role, ch), size)
        d.text((x, base), ch, font=f, fill=color + (255,), anchor="ls")
        x += w + spacing
    bbox = img.getbbox() or (0, 0, 1, 1)
    # по вертикали держим метрики шрифта, чтобы строки разной высоты стояли ровно
    asc = _font(FONTS[role][0], size).getmetrics()[0]
    top = base - int(asc * 0.78)
    bottom = base + int(size * 0.28)
    img = img.crop((bbox[0], min(top, bbox[1]), bbox[2], max(bottom, bbox[3])))
    _text_cache[key] = img
    return img


def paste(layer, img, cx, cy, alpha=1.0, scale=1.0, anchor="c"):
    """Кладёт картинку на слой: anchor 'c' — по центру, 'l' — левым краем в cx."""
    if alpha <= 0:
        return
    if scale != 1.0:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                         Image.LANCZOS)
    if alpha < 1:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    x = int(round(cx - (img.width / 2 if anchor == "c" else 0)))
    y = int(round(cy - img.height / 2))
    layer.alpha_composite(img, (max(0, x), max(0, y)),
                          (max(0, -x), max(0, -y)))


def soft_shadow(layer, radius=18, opacity=0.55):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(radius))
    a = a.point(lambda v: int(min(255, v * opacity * 1.6)))
    sh = Image.new("RGBA", layer.size, BLACK + (0,))
    sh.putalpha(a)
    sh.alpha_composite(layer)
    return sh


# ---------------------------------------------------------------- графика

class Element:
    start = 0
    dur = 0
    sfx = None  # (имя, смещение в кадрах)
    shadow = True

    def active(self, k):
        return self.start <= k < self.start + self.dur

    def out_alpha(self, f, n=7):
        return clamp01((self.dur - f) / n)


class Hook(Element):
    """Хук, п. 7: капс-строка, линия 140 px, курсивный акцент."""

    def __init__(self, start, line1, line2, y=800, dur=75):
        self.start, self.dur, self.line1, self.line2, self.y = start, dur, line1, line2, y
        self.sfx = ("tick", 0)

    def draw(self, layer, f, ctx):
        out = self.out_alpha(f)
        l1 = text_image(self.line1, "inter600", 54, TEXT, spacing=6)
        l2 = text_image(self.line2, "lora", 104, ACCENT)
        y1 = self.y - 70
        y2 = self.y + 62
        paste(layer, l1, W / 2, y1, alpha=ease_out((f - 1) / 9) * out)
        lw = 140 * ease_out((f - 4) / 12)
        if lw > 1:
            d = ImageDraw.Draw(layer)
            a = int(255 * out)
            d.rectangle([W / 2 - lw / 2, self.y - 17, W / 2 + lw / 2, self.y - 15], fill=BEIGE + (a,))
        p = ease_out((f - 6) / 10)
        paste(layer, l2, W / 2, y2 + 18 * (1 - p), alpha=p * out)


class Plate(Element):
    """Плашка раздела: капсула, рамка, бордовая точка, капс Inter Medium 30."""

    def __init__(self, start, text, x=90, y=330, dur=66):
        self.start, self.dur, self.text, self.x, self.y = start, dur, text, x, y
        self.sfx = ("tick", 0)
        self.shadow = False

    def draw(self, layer, f, ctx):
        out = self.out_alpha(f)
        t = text_image(self.text, "inter500", 30, TEXT, spacing=5)
        h = 66
        pad, dot_r, gap = 28, 6, 18
        full = pad + 2 * dot_r + gap + t.width + pad
        w = max(h, full * ease_out(f / 14))
        cap = Image.new("RGBA", (int(full) + 8, h + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(cap)
        d.rounded_rectangle([4, 4, 4 + w, 4 + h], radius=h // 2,
                            fill=BLACK + (int(255 * 0.75),), outline=BEIGE + (255,), width=2)
        cy = 4 + h / 2
        d.ellipse([4 + pad, cy - dot_r, 4 + pad + 2 * dot_r, cy + dot_r], fill=BORDO + (255,))
        ta = ease_out((f - 6) / 8)
        if ta > 0:
            txt = Image.new("RGBA", cap.size, (0, 0, 0, 0))
            paste(txt, t, 4 + pad + 2 * dot_r + gap, cy + 1, alpha=ta, anchor="l")
            # текст не выходит за раскрывшуюся капсулу
            mask = Image.new("L", cap.size, 0)
            ImageDraw.Draw(mask).rectangle([0, 0, 4 + w - pad / 2, cap.height], fill=255)
            txt.putalpha(Image.fromarray(np.minimum(np.array(txt.getchannel("A")), np.array(mask))))
            cap.alpha_composite(txt)
        paste(layer, cap, self.x - 4, self.y, alpha=out, anchor="l")


class Ring(Element):
    """Кольцо удара: расходится за 0,5 сек."""

    def __init__(self, start, src_point, dur=15):
        self.start, self.dur, self.src_point = start, dur, src_point
        self.shadow = False

    def draw(self, layer, f, ctx):
        x, y = ctx["map"](self.src_point)
        p = ease_out(f / self.dur)
        r = 18 + 190 * p
        a = int(230 * (1 - p) ** 1.3)
        d = ImageDraw.Draw(layer)
        wdt = max(1, int(round(3 - 1.5 * p)))
        d.ellipse([x - r, y - r, x + r, y + r], outline=TEXT + (a,), width=wdt)


class Callout(Element):
    """Выноска: точка + кружок на объекте, линия к подписи (Lora 62 + капс)."""

    def __init__(self, start, dur, track, title, caps, label_xy=(600, 600)):
        self.start, self.dur, self.track = start, dur, track  # track: {out_frame: (x, y) src}
        self.title, self.caps, self.label_xy = title, caps, label_xy
        self.sfx = ("tick", 0)

    def draw(self, layer, f, ctx):
        k = self.start + f
        sp = self.track.get(k) or self.track[min(self.track, key=lambda q: abs(q - k))]
        x, y = ctx["map"](sp)
        out = self.out_alpha(f)
        d = ImageDraw.Draw(layer)
        p = ease_out(f / 8)
        a = int(255 * out)
        if p > 0:
            r = 26 * (0.6 + 0.4 * p)
            d.ellipse([x - r, y - r, x + r, y + r], outline=TEXT + (int(a * p),), width=3)
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=BORDO + (int(a * p),))
        lx, ly = self.label_xy
        end = (lx - 18, ly + 32)
        vx, vy = end[0] - x, end[1] - y
        L = math.hypot(vx, vy)
        q = ease_out((f - 6) / 12)
        if q > 0 and L > 30:
            sx, sy = x + vx / L * 30, y + vy / L * 30
            ex, ey = sx + (end[0] - sx) * q, sy + (end[1] - sy) * q
            d.line([sx, sy, ex, ey], fill=TEXT + (a,), width=3)
        t = ease_out((f - 14) / 12)
        if t > 0:
            ti = text_image(self.title, "lora", 62, ACCENT)
            ci = text_image(self.caps, "inter500", 30, TEXT, spacing=5)
            paste(layer, ti, lx, ly + 10 * (1 - t), alpha=t * out, anchor="l")
            paste(layer, ci, lx + 2, ly + 66 + 10 * (1 - t), alpha=t * out, anchor="l")


class Subtitles(Element):
    """Субтитры по словам, п. 6. words: [(out_frame_start, out_frame_end, text, accent)]."""

    def __init__(self, words, underline_word=None):
        self.words = words
        self.underline_word = underline_word
        self.start = min((w[0] for w in words), default=0)
        self.dur = max((w[1] for w in words), default=0) - self.start

    def draw(self, layer, f, ctx):
        k = self.start + f
        for i, (a, b, text, accent) in enumerate(self.words):
            if not (a <= k < b):
                continue
            g = k - a
            p = ease_out(g / 4)
            img = (text_image(text, "lora", 92, ACCENT) if accent
                   else text_image(text, "inter600", 76, TEXT))
            if img.width > 870:
                img = img.resize((870, int(img.height * 870 / img.width)), Image.LANCZOS)
            paste(layer, img, W / 2, 1240 + 12 * (1 - p), alpha=p, scale=0.92 + 0.08 * p)
            if self.underline_word == i:
                u = ease_out(g / 10)
                d = ImageDraw.Draw(layer)
                x0 = W / 2 - img.width / 2
                d.rectangle([x0, 1240 + img.height / 2 + 6, x0 + img.width * u,
                             1240 + img.height / 2 + 8], fill=BEIGE + (255,))


# ---------------------------------------------------------------- таймлайн

class Segment:
    def __init__(self, src_in, src_out, zoom, center, trans_in="cut"):
        self.fin = round(src_in * FPS)
        self.fout = round(src_out * FPS)
        self.zoom = zoom          # функция (кадр внутри отрезка, длина) -> (масштаб, dx, dy)
        self.center = center      # центр зума в координатах исходника
        self.trans_in = trans_in  # 'cut' | 'dissolve'
        self.out_start = 0

    @property
    def length(self):
        return self.fout - self.fin


def layout(segments):
    t = 0
    for i, s in enumerate(segments):
        if i and s.trans_in == "dissolve":
            t -= DISSOLVE
        s.out_start = t
        t += s.length
    return t


def src2out(segments, i, src_time):
    s = segments[i]
    return s.out_start + round(src_time * FPS) - s.fin


def slow_push(a, b):
    return lambda f, n: (a + (b - a) * ease_in_out(f / max(1, n - 1)), 0, 0)


# ---------------------------------------------------------------- звук

def tone_tick():
    t = np.arange(int(0.06 * SR)) / SR
    s = np.sin(2 * np.pi * 2400 * t) * 0.6 + np.sin(2 * np.pi * 3700 * t) * 0.3
    return s * np.exp(-t * 90)


def tone_rustle(seed=1):
    rng = np.random.default_rng(seed)
    n = int(0.4 * SR)
    x = rng.standard_normal(n)
    # грубая полосовая фильтрация: разность двух сглаживаний
    k1, k2 = np.ones(3) / 3, np.ones(24) / 24
    x = np.convolve(x, k1, "same") - np.convolve(x, k2, "same")
    t = np.arange(n) / n
    return x * np.sin(np.pi * t) ** 2


def tone_boom():
    t = np.arange(int(0.7 * SR)) / SR
    f = 48 + 50 * np.exp(-t * 14)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 6.5)
    s[:240] *= np.linspace(0, 1, 240)
    return s


def norm_peak(x, db):
    return x / (np.abs(x).max() + 1e-9) * 10 ** (db / 20)


SFX = {
    "tick": lambda: norm_peak(tone_tick(), -32),
    "rustle": lambda: norm_peak(tone_rustle(), -22),
    "boom": lambda: norm_peak(tone_boom(), -12),
}


def build_audio(src, segments, total, sfx_events, workdir):
    voice = os.path.join(workdir, "voice_src.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", str(SR),
         "-af", VOICE_CHAIN, "-c:a", "pcm_f32le", voice])
    raw = np.frombuffer(subprocess.run(
        ["ffmpeg", "-v", "error", "-i", voice, "-f", "f32le", "-"],
        check=True, capture_output=True).stdout, dtype=np.float32)
    out = np.zeros(total * SPF + SR, dtype=np.float64)
    micro = int(0.012 * SR)
    xf = DISSOLVE * SPF
    for i, s in enumerate(segments):
        a, b = s.fin * SPF, s.fout * SPF
        clip = raw[a:b].astype(np.float64).copy()
        env = np.ones(len(clip))
        nxt = segments[i + 1] if i + 1 < len(segments) else None
        if s.trans_in == "dissolve" and i:
            env[:xf] = np.sin(np.linspace(0, np.pi / 2, xf))
        else:
            env[:micro] = np.linspace(0, 1, micro)
        if nxt is not None and nxt.trans_in == "dissolve":
            env[-xf:] = np.cos(np.linspace(0, np.pi / 2, xf))
        else:
            env[-micro:] = np.minimum(env[-micro:], np.linspace(1, 0, micro))
        o = s.out_start * SPF
        out[o:o + len(clip)] += clip * env
    voice_only = out[:total * SPF].copy()
    for name, frame in sfx_events:
        x = SFX[name]()
        o = int(frame * SPF)
        n = min(len(x), len(out) - o)
        out[o:o + n] += x[:n]
    out = out[:total * SPF]
    return voice_only.astype(np.float32), out.astype(np.float32)


def write_wav(path, x, extra_filter=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-"]
    if extra_filter:
        cmd += ["-af", extra_filter]
    cmd += ["-ac", "2", "-c:a", "pcm_s24le", path]
    subprocess.run(cmd, input=x.tobytes(), check=True)


def loudnorm(path_in, path_out):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path_in, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    flt = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
           f"measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
           f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:"
           f"offset={j['target_offset']}")
    run(["ffmpeg", "-v", "error", "-y", "-i", path_in, "-af", flt, "-ar", str(SR),
         "-c:a", "pcm_s24le", path_out])


# ---------------------------------------------------------------- видео

def decode_graded(src, frames_needed):
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps={FPS},{GRADE}",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H * 3
    frames, n = {}, 0
    last = max(frames_needed)
    while n <= last:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        if n in frames_needed:
            frames[n] = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        n += 1
    p.stdout.close()
    p.wait()
    # исходник может кончиться на кадр раньше расчётного
    for k in frames_needed:
        if k not in frames:
            frames[k] = frames[max(frames)]
    return frames


def vignette_mask():
    gray = np.full((H, W, 3), 128, np.uint8)
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                        "-s", f"{W}x{H}", "-i", "-", "-vf", f"format=yuv444p,{VIGNETTE},format=bgr24",
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       input=gray.tobytes(), capture_output=True, check=True)
    m = np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3)[..., 1].astype(np.float32) / 128
    return m[..., None]


def transform(img, scale, center, dx=0, dy=0):
    cx, cy = center
    M = np.float32([[scale, 0, cx - scale * cx + dx], [0, scale, cy - scale * cy + dy]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return out, (lambda p: (cx + (p[0] - cx) * scale + dx, cy + (p[1] - cy) * scale + dy))


def render(src, segments, elements, sfx_events, out_path, workdir, extras=None):
    os.makedirs(workdir, exist_ok=True)
    total = layout(segments)
    needed = set()
    for s in segments:
        needed.update(range(s.fin, s.fout))
    print(f"[render] {total} кадров ({total / FPS:.2f} с), декодирование…", file=sys.stderr)
    frames = decode_graded(src, needed)
    vmask = vignette_mask()
    rng = np.random.default_rng(7)

    voice, mix = build_audio(src, segments, total, sfx_events, workdir)
    write_wav(os.path.join(workdir, "mix_pre.wav"), mix)
    loudnorm(os.path.join(workdir, "mix_pre.wav"), os.path.join(workdir, "mix.wav"))
    clean = os.path.splitext(out_path)[0] + "_voice.wav"
    write_wav(os.path.join(workdir, "voice_pre.wav"), voice)
    loudnorm(os.path.join(workdir, "voice_pre.wav"), clean)

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", os.path.join(workdir, "mix.wav"),
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-movflags", "+faststart",
         "-shortest", out_path], stdin=subprocess.PIPE)

    for k in range(total):
        acc, wsum, ctx_map = None, 0.0, None
        for s in segments:
            f = k - s.out_start
            if not (0 <= f < s.length):
                continue
            sc, dx, dy = s.zoom(f, s.length)
            img, mp = transform(frames[s.fin + f], sc, s.center, dx, dy)
            if s.trans_in == "dissolve" and f < DISSOLVE and acc is not None:
                w = (f + 1) / (DISSOLVE + 1)
                acc = acc * (1 - w) + img.astype(np.float32) * w
            else:
                acc = img.astype(np.float32)
            ctx_map = mp  # графика привязана к входящему плану
        frame = acc * vmask
        frame += rng.integers(-3, 4, size=(H, W, 1)).astype(np.float32)
        frame = np.clip(frame, 0, 255).astype(np.uint8)

        act = [e for e in elements if e.active(k)]
        if act:
            ctx = {"map": ctx_map}
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            flat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for e in act:
                e.draw(layer if e.shadow else flat, k - e.start, ctx)
            if layer.getbbox():
                layer = soft_shadow(layer)
            layer.alpha_composite(flat)
            g = np.asarray(layer).astype(np.float32)
            a = g[..., 3:4] / 255
            rgb = g[..., 2::-1]  # RGBA -> BGR
            frame = (frame * (1 - a) + rgb * a).astype(np.uint8)
        enc.stdin.write(np.ascontiguousarray(frame).tobytes())
        if k % 60 == 0:
            print(f"[render] {k}/{total}", file=sys.stderr)
    enc.stdin.close()
    enc.wait()
    return total


def track_point(src, frame_from, frame_to, start_xy, patch=(150, 90), search=90):
    """Простейший трекинг точки шаблоном (кадр к кадру) по исходнику."""
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps={FPS}",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H
    n, pts = 0, {}
    x, y = start_xy
    pw, ph = patch
    tmpl = None
    while n <= frame_to:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        if n >= frame_from:
            g = cv2.GaussianBlur(np.frombuffer(buf, np.uint8).reshape(H, W), (5, 5), 0)
            if tmpl is None:
                tmpl = g[int(y - ph / 2):int(y + ph / 2), int(x - pw / 2):int(x + pw / 2)]
            else:
                x0 = int(max(0, x - pw / 2 - search)); y0 = int(max(0, y - ph / 2 - search))
                x1 = int(min(W, x + pw / 2 + search)); y1 = int(min(H, y + ph / 2 + search))
                res = cv2.matchTemplate(g[y0:y1, x0:x1], tmpl, cv2.TM_CCOEFF_NORMED)
                _, _, _, loc = cv2.minMaxLoc(res)
                x, y = x0 + loc[0] + pw / 2, y0 + loc[1] + ph / 2
                tmpl = g[int(y - ph / 2):int(y + ph / 2), int(x - pw / 2):int(x + pw / 2)]
            pts[n] = (x, y)
        n += 1
    p.stdout.close()
    p.wait()
    # сглаживание, чтобы выноска не дрожала
    ks = sorted(pts)
    xs = np.array([pts[k][0] for k in ks]); ys = np.array([pts[k][1] for k in ks])
    ker = np.ones(5) / 5
    xs = np.convolve(np.pad(xs, 2, mode="edge"), ker, "valid")
    ys = np.convolve(np.pad(ys, 2, mode="edge"), ker, "valid")
    return {k: (float(a), float(b)) for k, a, b in zip(ks, xs, ys)}
