"""Ролик по референсу «Greatest transition ever»: игровое видео (Minecraft) в центре кадра с чёрными
полями и подписью сверху → игрок ломает блок, в зелёном блоке (хромакей) появляется реальное видео →
камера «ныряет» в блок → реальное видео на весь экран. Без цветокоррекции и плашек нашего стиля.

Запуск: python3 projects/2026-10-13_minecraft.py папка_с_исходниками [папка_вывода]
Исходники: intro.mp4 («маин вступление», 2304×1440), main2.mp4 («для маина 2», 1440×2560).
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402  (только звук и шрифты)
import kinetic  # noqa: E402,F401  (регистрирует «вжух»)

SRC_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
INTRO = os.path.join(SRC_DIR, "intro.mp4")
MAIN = os.path.join(SRC_DIR, "main2.mp4")
NAME = "2026-10-13_майнкрафт_v1"
CAPTION = "Лучший переход 💀😂"

W, H, FPS = 1080, 1920, 30
GW, GH = 2304, 1440                 # кадр игры
MW, MH = 1440, 2560                 # реальное видео
GREEN_BOX = (1018, 468, 1383, 843)  # зелёный блок в кадре игры (x0, y0, x1, y1)
GC = ((GREEN_BOX[0] + GREEN_BOX[2]) / 2, (GREEN_BOX[1] + GREEN_BOX[3]) / 2)
GSIDE_H = GREEN_BOX[3] - GREEN_BOX[1]
GSIDE_W = GREEN_BOX[2] - GREEN_BOX[0]

T_GREEN = 7.60      # блок открылся — в нём начинается реальное видео
T_ZOOM0 = 7.95      # начало «нырка»
T_ZOOM1 = 8.40      # конец «нырка» — дальше реальное видео на весь экран
SETTLE = 12         # кадров: реальное видео «оседает» к ×1
S0 = W / GW                          # масштаб игры в letterbox
S1 = H / (GSIDE_H - 8) * 1.02        # к концу нырка зелёный блок перекрывает весь экран
MAIN_IN_SRC_H = GSIDE_W * 16 / 9 * 1.04  # реальное видео внутри блока: 9:16, перекрывает блок по ширине


def frames(path, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)


def green_mask(f):
    f = f.astype(np.int16)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    msk = ((g > 45) & (g > r * 1.6) & (g > b * 2.5)).astype(np.uint8) * 255
    roi = np.zeros_like(msk)
    x0, y0, x1, y1 = GREEN_BOX
    roi[y0 - 25:y1 + 25, x0 - 25:x1 + 25] = 255
    msk = cv2.bitwise_and(msk, roi)
    msk = cv2.morphologyEx(msk, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    msk = cv2.dilate(msk, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(msk, (5, 5), 0)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def game_affine(t):
    """Аффинное преобразование кадр игры → выход: s, центр в источнике."""
    p = ease((t - T_ZOOM0) / (T_ZOOM1 - T_ZOOM0))
    s = math.exp(math.log(S0) + (math.log(S1) - math.log(S0)) * p)
    # центр движется к блоку быстрее, чем растёт масштаб (иначе блок «уезжает» из кадра)
    q = min(1.0, p * 1.6)
    cx = GW / 2 + (GC[0] - GW / 2) * q
    cy = GH / 2 + (GC[1] - GH / 2) * q
    return s, cx, cy


def mat(s, cx, cy):
    return np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])


def caption_layer():
    img = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(os.path.join(m.FONT_DIR, "inter-cyrillic-600-normal.ttf"), 46)
    emo = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    text, emojis = CAPTION.split(" 💀")[0] + " ", "💀😂"
    tw = d.textlength(text, font=font)
    em = Image.new("RGBA", (260, 140), (0, 0, 0, 0))
    ImageDraw.Draw(em).text((0, 0), emojis, font=emo, embedded_color=True)
    em = em.crop(em.getbbox()).resize((96, 46), Image.LANCZOS)
    x = (W - tw - em.width) / 2
    d.text((x, 80), text, font=font, fill=(255, 255, 255, 255), anchor="lm")
    img.alpha_composite(em, (int(x + tw), 80 - em.height // 2))
    return np.asarray(img)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    work = os.path.join(OUT_DIR, "_work")
    os.makedirs(work, exist_ok=True)

    n_intro = round(T_ZOOM1 * FPS)
    main_frames = list(frames(MAIN, MW, MH))
    n_main = len(main_frames)
    k_main0 = round(T_GREEN * FPS)                 # кадр ролика, где начинается main2
    total = k_main0 + n_main
    cap = caption_layer()
    cap_y = int(H / 2 - GH * S0 / 2) - 150

    # ---------------------------------------------------------------- звук
    def pcm(path, ss=0):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", path, "-ac", "1", "-ar", str(m.SR),
                            "-f", "f32le", "-"], capture_output=True, check=True)
        return np.frombuffer(r.stdout, np.float32).astype(np.float64)

    spf = m.SR // FPS
    mix = np.zeros(total * spf + m.SR)
    a_intro = pcm(INTRO)[:n_intro * spf] * 10 ** (14 / 20)    # звук игры тихий — поднимаем
    fo = int(0.25 * m.SR)
    a_intro[-fo:] *= np.linspace(1, 0, fo)
    mix[:len(a_intro)] += a_intro
    a_main = pcm(MAIN)
    fi = int(0.12 * m.SR)
    a_main[:fi] *= np.linspace(0, 1, fi)
    o = k_main0 * spf
    mix[o:o + len(a_main)] += a_main[:len(mix) - o]
    wh = m.SFX["whoosh"]() * 2.0
    o = round(T_ZOOM0 * FPS) * spf
    mix[o:o + len(wh)] += wh
    mix = mix[:total * spf].astype(np.float32)
    m.write_wav(os.path.join(work, "mc_pre.wav"), mix)
    m.loudnorm(os.path.join(work, "mc_pre.wav"), os.path.join(work, "mc.wav"))

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", os.path.join(work, "mc.wav"), "-c:v", "libx264", "-preset", "slow", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out],
        stdin=subprocess.PIPE)

    # ---------------------------------------------------------------- 1. игра → нырок в блок
    for k, g in enumerate(frames(INTRO, GW, GH)):
        if k >= n_intro:
            break
        t = k / FPS
        s, cx, cy = game_affine(t)
        M = mat(s, cx, cy)
        frame = cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        if k >= k_main0:
            gm = green_mask(g)
            # с началом нырка окно плавно становится сплошным: выпавшие блоки игры не висят поверх видео
            fill = ease((t - T_ZOOM0 + 0.05) / 0.2)
            if fill > 0:
                x0, y0, x1, y1 = GREEN_BOX
                rect = np.zeros_like(gm)
                rect[y0:y1, x0:x1] = 255
                rect = cv2.GaussianBlur(rect, (9, 9), 0)
                gm = np.maximum(gm, (rect * fill).astype(np.uint8))
            a = cv2.warpAffine(gm, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
            mf = main_frames[k - k_main0]
            sm = s * MAIN_IN_SRC_H / MH                  # масштаб реального видео в выходе
            mx, my = W / 2 + s * (GC[0] - cx), H / 2 + s * (GC[1] - cy)
            Mm = np.float32([[sm, 0, mx - sm * MW / 2], [0, sm, my - sm * MH / 2]])
            mv = cv2.warpAffine(mf, Mm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            frame = (frame * (1 - a) + mv * a).astype(np.uint8)
        # подпись сверху — уходит с началом нырка
        ca = 1.0 - min(1.0, max(0.0, (t - T_ZOOM0) / 0.1))
        if ca > 0:
            reg = frame[cap_y:cap_y + cap.shape[0]].astype(np.float32)
            al = cap[..., 3:4].astype(np.float32) / 255 * ca
            frame[cap_y:cap_y + cap.shape[0]] = (reg * (1 - al) + cap[..., :3] * al).astype(np.uint8)
        enc.stdin.write(np.ascontiguousarray(frame).tobytes())

    # ---------------------------------------------------------------- 2. реальное видео на весь экран
    s_end = S1 * MAIN_IN_SRC_H / MH * MH / H        # масштаб main2 относительно «на весь экран» в конце нырка
    for j in range(n_intro - k_main0, n_main):
        f = j - (n_intro - k_main0)
        z = 1 + (s_end - 1) * (1 - ease(f / SETTLE))
        sm = z * H / MH
        Mm = np.float32([[sm, 0, W / 2 - sm * MW / 2], [0, sm, H / 2 - sm * MH / 2]])
        frame = cv2.warpAffine(main_frames[j], Mm, (W, H), flags=cv2.INTER_AREA if z <= 1.01 else cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REPLICATE)
        enc.stdin.write(np.ascontiguousarray(frame).tobytes())

    enc.stdin.close()
    enc.wait()
    print(f"готово: {out}, {total / FPS:.2f} с; блок с {T_GREEN} с, нырок {T_ZOOM0}–{T_ZOOM1} с, "
          f"масштаб на стыке ×{s_end:.2f}")


if __name__ == "__main__":
    main()
