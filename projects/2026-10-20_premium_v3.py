"""«Премиум» v3 — моушн-ролик по референсу «iPhone 17 Pro — 3D Animation #blender» (Naimorphic Studio).

Кошелёк вырезан нейросетью (BiRefNet lite, ONNX, MIT; модель — с релизов rembg на GitHub) и живёт
как объект: летает, крутится, переворачивается, по нему идут блики и свечение — как телефон в референсе.
Крупные планы — настоящее видео, тоже вырезанное покадрово (реальный объём и блики), на чёрном.

  0,00–1,20  чёрный, маленький кошелёк в центре; на 0,65 «включается» оранжевое свечение по контуру
  1,20–3,65  резкий наезд: ребро кошелька вплотную, поворот, тёплый свет (видео 900,7 с, ×0,5)
  3,70–7,45  крупно угол кошелька, светлый, поворот ~30° с наездом, блик, свет гаснет (видео 113,0 с, ×0,5)
  7,50–11,25 два кошелька рядом, свет поднимается снизу и заливает их, гаснет
  11,28–16,40 светлая студия, каменный «пол»; кошелёк парит, оборот 360° вокруг оси, сзади выезжает второй;
             сверху «◆ PREMIUM», слева мелкая подпись
  16,43–17,53 знак на чёрном

Звук — из референса (по просьбе заказчика; при публикации возможна претензия по правам на трек).

Запуск: python3 projects/2026-10-20_premium_v3.py IMG_7542.MOV референс.mp4 [папка_вывода]
"""
import math
import os
import subprocess
import sys
import urllib.request

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402  (шрифты, −14 LUFS)

SRC = sys.argv[1] if len(sys.argv) > 1 else "IMG_7542.MOV"
REF = sys.argv[2] if len(sys.argv) > 2 else "ref.mp4"
OUT_DIR = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "output"
NAME = "2026-10-20_премиум_v3"
WORK = os.path.join(OUT_DIR, "_work", "premium_v3")
MODEL_URL = ("https://github.com/danielgatis/rembg/releases/download/v0.0.0/"
             "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx")
W, H, FPS, SFPS = 1080, 1920, 30, 60
TOTAL, LOGO_T = 17.53, 16.43
ORANGE = np.array([0.20, 0.45, 1.0], np.float32)   # BGR

# кадры-вырезки (с исходника): главный ракурс, сбоку, пол
STILLS = {"hero": 891.0, "side": 82.0}
GROUND_T = 365.0
# видео для крупных планов: (начало, длительность в ролике, скорость)
CLIPS = {"edge": (900.7, 2.45, 0.5), "corner": (113.0, 3.75, 0.5)}
DARK_MASK = {"corner"}   # маска по яркости вместо нейросети


# ------------------------------------------------------------------ утилиты
def clamp01(x):
    return float(min(1.0, max(0.0, x)))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp01(x)) ** 3


def ramp(t, t0, t1):
    return smooth((t - t0) / (t1 - t0))


def lerp(a, b, k):
    return a + (b - a) * k


def grab(t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3).copy()


# ------------------------------------------------------------------ вырезка
_sess = None


def seg(bgr):
    """Маска объекта 0..1 (BiRefNet lite)."""
    global _sess
    if _sess is None:
        import onnxruntime as ort
        path = os.path.join(WORK, "birefnet_lite.onnx")
        if not os.path.exists(path):
            os.makedirs(WORK, exist_ok=True)
            urllib.request.urlretrieve(MODEL_URL, path)
        so = ort.SessionOptions()
        so.enable_cpu_mem_arena = False   # иначе память растёт с каждым кадром
        _sess = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
    x = cv2.resize(bgr[..., ::-1], (1024, 1024), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    o = _sess.run(None, {"input_image": x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    o = 1 / (1 + np.exp(-o))
    return cv2.resize(o, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR)


def no_stone(bgr, a):
    """Убирает из маски светлый гранит, если модель его захватила (кошелёк чёрный)."""
    y = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255, (0, 0), 6)
    return a * np.clip((0.42 - y) / 0.12, 0, 1)


def dark_mask(bgr):
    """Маска по яркости для крупных планов, где нейросеть путает кошелёк и камень:
    кошелёк — тёмная область, блики чешуи заливаются морфологией."""
    y = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255, (0, 0), 9)
    a = (y < 0.30).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81)))
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        a = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    # ровный край: сглаживание контура
    a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 9)
    return np.clip((a - 0.5) * 3 + 0.5, 0, 1)


class Obj:
    """Вырезанный объект: цвет (0..1, BGR) и альфа, обрезанные по рамке."""

    def __init__(self, bgr, a, pad=40):
        ys, xs = np.where(a > 0.3)
        x0, x1 = max(0, xs.min() - pad), min(a.shape[1], xs.max() + pad)
        y0, y1 = max(0, ys.min() - pad), min(a.shape[0], ys.max() + pad)
        self.rgb = look_leather(bgr[y0:y1, x0:x1])
        self.a = a[y0:y1, x0:x1].astype(np.float32)
        self.h, self.w = self.a.shape


def still_obj(name):
    path = os.path.join(WORK, f"cut_{name}.npz")
    if not os.path.exists(path):
        f = grab(STILLS[name])
        a = no_stone(f, seg(f))
        np.savez_compressed(path, f=f, a=(a * 255).astype(np.uint8))
    d = np.load(path)
    return Obj(d["f"], d["a"].astype(np.float32) / 255)


def clip_frames(name):
    """Стабилизированный клип (60 к/с) и маски по кадрам — кэш на диске."""
    src, dur, speed = CLIPS[name]
    span = dur * speed + 0.3
    mp4 = os.path.join(WORK, f"clip_{name}.mp4")
    if not os.path.exists(mp4):
        trf = mp4[:-4] + ".trf"
        common = ["-ss", f"{src:.3f}", "-t", f"{span:.3f}", "-i", SRC]
        m.run(["ffmpeg", "-v", "error", "-y", *common, "-vf",
               f"vidstabdetect=shakiness=6:accuracy=15:result={trf}", "-f", "null", "-"])
        m.run(["ffmpeg", "-v", "error", "-y", *common, "-vf",
               f"vidstabtransform=input={trf}:smoothing=45:optzoom=1:interpol=bicubic,fps={SFPS}",
               "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-an", mp4])
    npz = os.path.join(WORK, f"clip_{name}.npz")
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                       capture_output=True, check=True).stdout
    frames = np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
    n = int(dur * speed * SFPS) + 2
    frames = frames[:n]
    if not os.path.exists(npz):
        masks = []
        for i, f in enumerate(frames):
            a = dark_mask(f) if name in DARK_MASK else no_stone(f, seg(f))
            masks.append((a * 255).astype(np.uint8))
            if i % 20 == 0:
                print(f"  маски {name}: {i}/{len(frames)}", flush=True)
        np.savez_compressed(npz, a=np.array(masks))
    return frames, np.load(npz)["a"]


# ------------------------------------------------------------------ свет
def look_leather(bgr):
    """Чёрная кожа → «рендер»: светлее, фактура рельефнее, цвет приглушён."""
    f = bgr.astype(np.float32) / 255
    y = f[..., 2] * 0.299 + f[..., 1] * 0.587 + f[..., 0] * 0.114
    det = y - cv2.GaussianBlur(y, (0, 0), 5)
    big = y - cv2.GaussianBlur(y, (0, 0), 30)
    yo = np.clip(0.05 + 1.55 * y + 1.5 * det + 0.5 * big, 0, 1)
    tint = f - y[..., None]
    return np.clip(yo[..., None] + tint * 0.35, 0, 1)


def ridge_of(rgb):
    y = rgb.mean(2)
    return np.clip((y - cv2.GaussianBlur(y, (0, 0), 3)) * 8, 0, 1)


def lit(rgb, a, sweep=None, warm=0.0, gain=1.0, rim=0.0, rim_color=ORANGE):
    """Свет на объекте в его системе координат.
    sweep = (позиция 0..1, угол, сила, цвет) — полоса блика; warm — оранжевый на гребнях; rim — контур."""
    out = rgb * gain
    h, w = a.shape
    if sweep:
        pos, ang, k, col = sweep
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        aa = math.radians(ang)
        d = (xx / w - 0.5) * math.cos(aa) + (yy / h - 0.5) * math.sin(aa)
        band = np.exp(-((d - lerp(-0.9, 0.9, pos)) / 0.13) ** 2)
        out = out + (band * k * (0.35 + ridge_of(rgb)))[..., None] * col
    if warm > 0:
        out = out + (ridge_of(rgb) * warm)[..., None] * ORANGE * 0.6
    if rim > 0:
        er = cv2.erode(a, np.ones((9, 9), np.uint8))
        edge = cv2.GaussianBlur(np.clip(a - er, 0, 1), (0, 0), 3)
        out = out + (edge * rim)[..., None] * rim_color
    return out


def place(canvas, rgb, a, cx, cy, scale, rot=0.0, spin=0.0, glow=0.0, glow_color=ORANGE, blur=0):
    """Кладёт объект на холст: центр, масштаб, поворот, оборот вокруг вертикальной оси (spin, градусы)
    с толщиной на ребре; glow — свечение вокруг."""
    h, w = a.shape
    c = math.cos(math.radians(spin))
    sgn = 1 if c >= 0 else -1
    if sgn < 0:   # обратная сторона — зеркально и чуть темнее
        rgb, a = rgb[:, ::-1] * 0.8, a[:, ::-1]
    rgb, a = np.ascontiguousarray(rgb, np.float32), np.ascontiguousarray(a, np.float32)
    sx = max(abs(c), 0.02)
    tilt = math.sin(math.radians(spin)) * 0.10       # перспектива: дальняя сторона ниже
    hw, hh = w / 2 * scale, h / 2 * scale
    # четыре угла (по часовой от левого верхнего) с перспективой
    near, far = 1 + tilt, 1 - tilt
    pts = np.float32([[-hw * sx, -hh * near], [hw * sx, -hh * far], [hw * sx, hh * far], [-hw * sx, hh * near]])
    r = math.radians(rot)
    R = np.float32([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
    pts = pts @ R.T + np.float32([cx, cy])
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(src, pts)
    layers = []
    thick = 0.035 * w * scale * abs(math.sin(math.radians(spin)))
    if thick > 1:   # ребро: тёмная копия со сдвигом
        side = -1 if math.sin(math.radians(spin)) * sgn > 0 else 1
        T = np.float32([[1, 0, side * thick], [0, 1, 0], [0, 0, 1]])
        layers.append((T @ M, 0.35))
    layers.append((M, 1.0))
    for Mi, k in layers:
        ai = cv2.warpPerspective(a, Mi, (W, H), flags=cv2.INTER_LINEAR)
        ci = cv2.warpPerspective(rgb, Mi, (W, H), flags=cv2.INTER_LINEAR) * k
        if blur > 1:
            kern = np.zeros((1, int(blur)), np.float32) + 1 / int(blur)
            ai = cv2.filter2D(ai, -1, kern)
            ci = cv2.filter2D(ci, -1, kern)
        if glow > 0 and k == 1.0:
            g = cv2.GaussianBlur(ai, (0, 0), 28) * glow
            canvas += g[..., None] * glow_color
        canvas[:] = canvas * (1 - ai[..., None]) + ci * ai[..., None]
    return canvas


def shadow(canvas, cx, cy, rx, ry, k):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    canvas *= 1 - (k * np.exp(-d * 2.2))[..., None]


# ------------------------------------------------------------------ фон «студия»
def studio_bg(ground):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # светлый центр сверху, края темнее — как серый фон в референсе
    d = np.sqrt(((xx - W * 0.55) / (W * 0.9)) ** 2 + ((yy - H * 0.30) / (H * 0.55)) ** 2)
    g = 0.78 - 0.55 * np.clip(d, 0, 1) ** 1.3
    bg = np.repeat(g[..., None], 3, 2).astype(np.float32)
    # «пол» из гранита: перспектива, ч/б, туман к горизонту
    gy = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    gy = gy[H // 3: H, :]
    hz = int(H * 0.70)
    src = np.float32([[0, 0], [W, 0], [W, gy.shape[0]], [0, gy.shape[0]]])
    dst = np.float32([[-W * 0.9, hz], [W * 1.9, hz], [W * 1.25, H + 60], [-W * 0.25, H + 60]])
    M = cv2.getPerspectiveTransform(src, dst)
    floor = cv2.warpPerspective(gy, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fl = np.clip((floor - 0.25) * 1.25, 0, 1) * 0.85
    fog = np.clip((yy - hz) / (H - hz), 0, 1)
    under = (yy >= hz).astype(np.float32)
    under = cv2.GaussianBlur(under, (0, 0), 6)
    fl = lerp(g * 0.9, fl * (0.55 + 0.25 * fog) + 0.05, fog ** 0.6)
    bg = bg * (1 - under[..., None]) + fl[..., None] * under[..., None]
    # мягкий «горизонт»
    bg *= 1 - 0.25 * np.exp(-((yy - hz) / 30) ** 2)[..., None]
    return bg


# ------------------------------------------------------------------ подписи
GREY = (220, 220, 220)


def diamond(size, width=3, color=GREY):
    img = Image.new("RGBA", (size * 2 + 8, size * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size + 4
    d.line([(c, c - size), (c + size, c), (c, c + size), (c - size, c), (c, c - size)],
           fill=color + (255,), width=width, joint="curve")
    s2 = int(size * 0.45)
    d.polygon([(c, c - s2), (c + s2, c), (c, c + s2), (c - s2, c)], fill=color + (255,))
    return img


def with_alpha(img, k):
    a = np.array(img)
    a[..., 3] = (a[..., 3] * k).astype(np.uint8)
    return Image.fromarray(a)


def text_layer(t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    used = False
    k = ramp(t, 13.8, 14.6) * (1 - ramp(t, 16.30, 16.40))
    if k > 0.01:
        used = True
        col = (60, 60, 60)
        word = m.text_image("PREMIUM", "mont600", 44, col, spacing=int(lerp(24, 13, k)))
        icon = diamond(16, 3, col)
        row = Image.new("RGBA", (icon.width + 18 + word.width, max(icon.height, word.height)), (0, 0, 0, 0))
        row.alpha_composite(icon, (0, (row.height - icon.height) // 2))
        row.alpha_composite(word, (icon.width + 18, (row.height - word.height) // 2))
        row = row.filter(ImageFilter.GaussianBlur(lerp(6, 0, k)))
        layer.alpha_composite(with_alpha(row, 0.85 * k), ((W - row.width) // 2, 250))
    k2 = ramp(t, 11.6, 12.0) * (1 - ramp(t, 13.3, 13.7))
    if k2 > 0.01:
        used = True
        for i, line in enumerate(("кожа крокодила", "ручная работа")):
            im = m.text_image(line, "inter500", 26, (70, 70, 70))
            layer.alpha_composite(with_alpha(im, 0.75 * k2), (72, 1150 + i * 36))
    if t >= LOGO_T:
        used = True
        k3 = ramp(t, LOGO_T, LOGO_T + 0.15)
        icon = diamond(34, 3)
        word = m.text_image("PREMIUM", "mont600", 26, GREY, spacing=10)
        layer.alpha_composite(with_alpha(icon, k3), ((W - icon.width) // 2, 900))
        layer.alpha_composite(with_alpha(word, k3 * 0.85), ((W - word.width) // 2, 900 + icon.height + 16))
    return layer if used else None


def overlay(frame, layer):
    if layer is None:
        return frame
    a = np.asarray(layer, np.float32) / 255
    return frame * (1 - a[..., 3:4]) + a[..., [2, 1, 0]] * a[..., 3:4]


def finish(f):
    glow = cv2.GaussianBlur(np.clip(f - 0.6, 0, 1), (0, 0), 20)
    return f + glow * 0.4


# ------------------------------------------------------------------ сцены
class Scenes:
    def __init__(self):
        self.hero = still_obj("hero")
        self.side = still_obj("side")
        self.edge = clip_frames("edge")
        self.corner = clip_frames("corner")
        self.studio = studio_bg(grab(GROUND_T))

    def video_obj(self, clip, t_local, speed):
        frames, a = clip
        i = min(len(frames) - 2, max(1, int(round(t_local * speed * SFPS))))
        # маска сглажена во времени — край не дрожит
        al = (a[i - 1].astype(np.float32) + 2 * a[i] + a[i + 1]) / (4 * 255)
        return look_leather(frames[i]), al

    def frame(self, t):
        cv = np.zeros((H, W, 3), np.float32)
        if t < 1.20:                                   # 1. маленький кошелёк в темноте, свет включается
            on = ramp(t, 0.62, 0.80)
            o = self.hero
            rgb = lit(o.rgb, o.a, warm=2.2 * on, gain=lerp(0.18, 0.55, on), rim=1.4 * on)
            place(cv, rgb, o.a, W / 2, H * 0.42, lerp(0.42, 0.45, t / 1.2), rot=-4, spin=lerp(-18, -12, t / 1.2),
                  glow=0.35 * on)
        elif t < 3.65:                                 # 2. ребро вплотную
            u = (t - 1.20) / 2.45
            rgb, a = self.video_obj(self.edge, t - 1.20, CLIPS["edge"][2])
            rgb = lit(rgb, a, warm=1.0, gain=1.1, rim=1.4,
                      sweep=(ease_out(u * 1.1), 60, 0.8, ORANGE * 0.9))
            z = lerp(1.30, 1.15, smooth(u)) * (1 + 0.25 * (1 - ease_out((t - 1.2) / 0.35)))
            place(cv, rgb, a, W * 0.47, H * 0.5, z, rot=lerp(-8, 6, smooth(u)), glow=0.25)
            cv *= 1 - ramp(t, 3.40, 3.65)
        elif t < 3.70:
            pass
        elif t < 7.45:                                 # 3. угол крупно, светлый, поворот
            u = (t - 3.70) / 3.75
            rgb, a = self.video_obj(self.corner, t - 3.70, CLIPS["corner"][2])
            rgb = lit(rgb, a, gain=1.45, rim=0.7, rim_color=np.array([1, 1, 1], np.float32),
                      sweep=(smooth(u), -30, 1.0, np.array([1, 1, 1], np.float32)), warm=0.3)
            z = lerp(1.05, 1.32, smooth(u)) * (1 + 0.15 * (1 - ease_out((t - 3.7) / 0.4)))
            place(cv, rgb, a, W * 0.5, H * 0.5, z, rot=lerp(-14, 16, smooth(u)))
            cv *= ramp(t, 3.70, 3.95) * (1 - ramp(t, 6.75, 7.42))
        elif t < 7.50:
            pass
        elif t < 11.25:                                # 4. два кошелька, свет снизу вверх
            u = (t - 7.50) / 3.75
            lvl = lerp(1.15, -0.25, ramp(t, 7.6, 10.0))
            wash = math.exp(-((t - 9.8) / 0.55) ** 2)
            for o, cx, cy, sc, rot, sp in ((self.side, W * 0.24, H * 0.60, 0.95, 78, 0),
                                           (self.hero, W * 0.71, H * 0.46, 1.05, -6, 14)):
                rgb = lit(o.rgb, o.a, gain=lerp(1.1, 1.6, wash), rim=0.8,
                          rim_color=np.array([1, 1, 1], np.float32), warm=0.2)
                # свет снизу: маска по высоте объекта
                hh = o.a.shape[0]
                yy = np.linspace(0, 1, hh, dtype=np.float32)[:, None]
                rgb = rgb * np.clip((yy - lvl) / 0.35 + 0.4, 0.04, 1)[..., None]
                place(cv, rgb, o.a, cx, cy - 140 * smooth(u), sc, rot=rot + 4 * u, spin=sp)
            cv *= 1 - ramp(t, 10.80, 11.22)
        elif t < LOGO_T:                               # 5. студия
            cv[:] = self.studio
            u = (t - 11.28) / (LOGO_T - 11.28)
            bob = math.sin((t - 11.28) * 1.6) * 14
            spin = 0.0
            if 11.95 <= t < 13.35:
                spin = 360 * smooth((t - 11.95) / 1.40)
            spin += lerp(-10, -22, smooth(u))
            push = lerp(0.86, 0.96, smooth(u))
            cy = H * 0.40 + bob
            # второй кошелёк выезжает сзади слева
            k2 = ease_out((t - 14.1) / 0.9)
            if k2 > 0:
                o = self.side
                rgb = lit(o.rgb, o.a, gain=1.0, rim=0.5, rim_color=np.array([1, 1, 1], np.float32))
                shadow(cv, W * lerp(0.5, 0.33, k2), H * 0.68, 210, 30, 0.35 * k2)
                place(cv, rgb * lerp(0.6, 1, k2), o.a, W * lerp(0.52, 0.34, k2), H * 0.43 + bob * 0.6,
                      0.50 * push / 0.66, rot=lerp(0, 72, k2), spin=20)
            o = self.hero
            shadow(cv, W * 0.56, H * 0.69, 320 * (1 - bob / 300), 40, 0.45)
            sw = (ramp(t, 13.3, 14.4), -25, 1.0, np.array([1, 1, 1], np.float32))
            rgb = lit(o.rgb, o.a, gain=1.15, rim=0.9, rim_color=np.array([1, 1, 1], np.float32),
                      sweep=sw, warm=0.5 * math.exp(-((t - 15.2) / 0.6) ** 2))
            fast = 11.95 <= t < 13.35
            if fast:   # смаз на обороте: среднее трёх положений
                acc = np.zeros_like(cv)
                for dt in (-1 / 90, 0, 1 / 90):
                    tt = t + dt
                    sp = 360 * smooth((tt - 11.95) / 1.40) + lerp(-10, -22, smooth(u))
                    c2 = cv.copy()
                    place(c2, rgb, o.a, W * 0.58, cy, push, rot=-3, spin=sp)
                    acc += c2
                cv[:] = acc / 3
            else:
                place(cv, rgb, o.a, W * 0.58, cy, push, rot=-3, spin=spin)
            cv = cv * lerp(0.0, 1.0, ramp(t, 11.28, 11.45))
        return overlay(finish(cv), text_layer(t))


def render_video(path):
    sc = Scenes()
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    for fi in range(int(round(TOTAL * FPS))):
        t = fi / FPS
        enc.stdin.write(np.clip(sc.frame(t) * 255, 0, 255).astype(np.uint8).tobytes())
        if fi % 60 == 0:
            print(f"{t:5.1f} с", flush=True)
    enc.stdin.close()
    enc.wait()


def main():
    os.makedirs(WORK, exist_ok=True)
    if "--stills" in sys.argv:   # проверочные кадры: --stills 0.9 2.0 ...
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]]
        sc = Scenes()
        tiles = [cv2.resize(np.clip(sc.frame(t) * 255, 0, 255).astype(np.uint8), (324, 576)) for t in ts]
        cv2.imwrite(os.path.join(WORK, "stills.jpg"), np.hstack(tiles))
        return
    v = os.path.join(WORK, NAME + "_video.mp4")
    a = os.path.join(WORK, NAME + "_audio.wav")
    render_video(v)
    raw = os.path.join(WORK, "ref_audio.wav")
    m.run(["ffmpeg", "-v", "error", "-y", "-i", REF, "-vn", "-ac", "2", "-ar", "48000", raw])
    m.loudnorm(raw, a)
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    m.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", out])
    print(out, f"{TOTAL:.2f} с")


if __name__ == "__main__":
    main()
