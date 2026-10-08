"""Ролик «обложка на паспорт: до и после ухода» — стиль как у «картхолдера» (текст по центру,
ч/б шторки, обратный зум в начале) + немного анимации по референсу: плашки-иконки и полоса прогресса.

Запуск: python3 projects/2026-10-08_oblozhka.py папка_с_рабочими_копиями [папка_вывода]
Рабочие копии: IMG_0490.mp4 (вы в кадре), IMG_0493.mp4 (руки + обложка) — SDR 1080×1920 30 к/с.

Структура:
  1. В кадре: «Эта кожа помнит всё, что с ней происходило» (дубль 5 из 5, 29,2 с).
  2. Закадровый голос поверх рук: «Вот так выглядела одна сторона после использования. А эту я решил
     немного восстановить» (36,8 с) + «Под воздействием тепла мелкие следы… менее заметными» (дубль 2, 53,5 с).
  3. В кадре: «Вот результат» (58,1 с) + «слева кожа после использования, справа после небольшого ухода»
     (последний дубль, 80,6 с).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402
import kinetic as kn  # noqa: E402
import placement as pl  # noqa: E402
from PIL import Image  # noqa: E402

SRC_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
TALK = os.path.join(SRC_DIR, "IMG_0490.mp4")
HANDS = os.path.join(SRC_DIR, "IMG_0493.mp4")
NAME = "2026-10-08_обложка_v2"
FPS = m.FPS

RAW = json.load(open(os.path.join(HERE, "cardholder2_raw.words.json"), encoding="utf-8"))["IMG_0490"]


def take(t0, t1, fix=None):
    ws = [dict(w) for w in RAW if t0 <= w["start"] < t1]
    if fix:
        ws[0]["start"] = fix  # распознавание растягивает первое слово дубля; начало — по звуку
    return ws


T = {
    "intro": take(28.8, 31.6, 29.25),
    "vo1": take(36.7, 41.9, 37.10),
    "vo2": take(53.0, 57.6, 53.60),
    "res": take(57.8, 58.8, 58.10),
    "fin": take(79.4, 84.59, 80.62),
}

SPEC = {
    "intro": [("эта кожа", 2), ("помнит всё", 2), ("что с ней", 3), ("происходило", 1)],
    "vo1": [("вот так", 2), ("выглядела", 1), ("одна сторона", 2), ("после использования", 2),
            ("а эту", 2), ("я решил", 2), ("немного", 1), ("восстановить", 1)],
    "vo2": [("под воздействием", 2), ("тепла", 1), ("мелкие следы", 2), ("на коже", 2),
            ("могут стать", 2), ("гораздо менее", 2), ("заметными", 1)],
    "res": [("вот результат", 2)],
    "fin": [("слева", 1), ("кожа", 1), ("после использования", 2), ("справа", 1),
            ("после небольшого ухода", 3)],
}
ACCENT = {"помнит всё", "восстановить", "заметными", "после небольшого ухода"}


def kf(*keys):
    return m.focus_zoom(m.keyframes(list(keys)), None)


def push(a, b, focus, pull=0.0, n=120):
    return kf((0, a, focus, pull, 1), (0, b, focus, pull, n))


segs = [
    # 1. в кадре; обратный зум ×1,30 → ×1,00 за 0,5 с
    m.Segment(29.20, 31.60, kf((0, 1.30, (540, 900), 0, 1), (0, 1.00, (540, 900), 0, 15),
                               (15, 1.05, (540, 900), 0, 60)), (540, 900)),
    # 2. закадровый голос поверх рук (картинка — IMG_0493)
    m.Segment(37.05, 39.86, push(1.05, 1.14, (540, 900)), None, video_in=36.0, video_file=HANDS),   # царапины
    m.Segment(39.90, 41.88, push(1.00, 1.06, (540, 900)), None, video_in=14.0, video_file=HANDS),   # гладкая
    m.Segment(53.50, 55.70, push(1.10, 1.18, (540, 860)), None, video_in=8.0, video_file=HANDS),    # царапины
    m.Segment(55.70, 57.62, push(1.00, 1.08, (540, 900)), None, video_in=24.5, video_file=HANDS),   # гладкая
    # «Вот результат» — поверх обложки крупно (в этот момент в кадре читаете с ноутбука);
    # после фразы короткая пауза (тихий кусок исходника 84,7 с), обложка держится ~1,6 с
    m.Segment(58.05, 58.98, push(1.00, 1.05, (540, 900)), None, video_in=40.0, video_file=HANDS),
    m.Segment(84.70, 85.40, push(1.05, 1.08, (540, 900)), None, video_in=40.93, video_file=HANDS),
    # 3. снова в кадре
    m.Segment(80.55, 84.65, push(1.00, 1.05, (540, 900)), (540, 900)),
]
total = m.layout(segs)


def out_of(t):
    fr = round(t * FPS)
    for s in segs:
        if s.fin <= fr < s.fout:
            return s.out_start + fr - s.fin
    nxt = [s for s in segs if s.fin > fr]
    return nxt[0].out_start if nxt else total


def wstart(key, word, nth=0):
    hits = [w for w in T[key] if w["word"].strip(",.!?").lower() == word]
    return hits[nth]["start"]


groups = []
for key, spec in SPEC.items():
    ws = T[key]
    assert sum(n for _, n in spec) == len(ws), (key, [w["word"] for w in ws])
    i = 0
    for text, n in spec:
        part = ws[i:i + n]
        i += n
        groups.append([out_of(part[0]["start"]), out_of(part[-1]["end"]) + 4, text, text in ACCENT])
groups.sort()
for i in range(len(groups) - 1):
    groups[i][1] = min(groups[i][1], groups[i + 1][0])
groups = [g for g in groups if g[1] - g[0] >= 4]


def grab(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", path, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return Image.frombytes("RGB", (m.W, m.H), r.stdout)


# высота текста под каждый план (не закрывать лицо и обложку целиком)
seg_y = pl.plan_y(segs, TALK, grab, os.path.join(OUT_DIR, "_work", "text_y_oblozhka.json"))
seg_y[0] = max(seg_y[0], 1150)  # в начале обложка в руках на уровне груди — текст ниже неё


def seg_index(k):
    last = 0
    for i, s in enumerate(segs):
        if s.out_start <= k < s.out_start + s.length:
            last = i
    return last


groups = [tuple(g[:4]) + (seg_y[seg_index(g[0] + 2)],) for g in groups]

# ---------------------------------------------------------------- анимации (по референсу, немного)
cut_vo, cut_res = segs[1].out_start, segs[7].out_start  # шторка — на возврате к вам в кадр
f_side = out_of(wstart("vo1", "одна"))
f_rest = out_of(wstart("vo1", "восстановить"))
f_fill0, f_fill1 = segs[3].out_start + 4, segs[4].out_start + segs[4].length - 8
f_left, f_right = out_of(wstart("fin", "слева")), out_of(wstart("fin", "справа"))

elements = [
    kn.WipeBar(cut_vo, color=kn.INK),
    kn.WipeBar(cut_res, color=kn.WHITE),
    # «…одна сторона после использования» — плашка над обложкой
    kn.Chip(f_side, segs[1].out_start + segs[1].length - 2 - f_side, "ПОСЛЕ ИСПОЛЬЗОВАНИЯ", "scratch",
            xy=(540, 420)),
    # «…решил немного восстановить» → «под воздействием тепла… менее заметными»: полоса прогресса
    kn.ProgressPanel(f_rest, segs[5].out_start - 3 - f_rest, "ВОССТАНОВЛЕНИЕ", "heat", xy=(540, 420),
                     fill_from=f_fill0, fill_to=f_fill1),
    # финал: показываете одну сторону, потом другую — плашки внизу, под текстом:
    # не закрывают ни лицо, ни обложку
    kn.Chip(f_left, f_right - f_left, "ПОСЛЕ ИСПОЛЬЗОВАНИЯ", "scratch", xy=(540, 1330)),
    kn.Chip(f_right, total + 10 - f_right, "ПОСЛЕ УХОДА", "check", xy=(540, 1330), dark=True),
    kn.KineticWords(groups, y=960, accent_color=kn.INK),
]
sfx = [(e.sfx[0], e.start) for e in elements if getattr(e, "sfx", None)]

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, NAME + ".mp4")
m.render(TALK, segs, elements, sfx, out, os.path.join(OUT_DIR, "_work"))

print(f"готово: {out}")
for i, s in enumerate(segs):
    print(f"  план {i + 1}: звук {s.fin / FPS:6.2f}–{s.fout / FPS:6.2f}, "
          f"картинка {os.path.basename(s.video_file or TALK)} {s.vin / FPS:6.2f} → "
          f"ролик {s.out_start / FPS:6.2f}–{(s.out_start + s.length) / FPS:6.2f}")
print("  высота текста по планам:", seg_y)
for a, b, t, acc, y in groups:
    print(f"  {a / FPS:6.2f}–{b / FPS:6.2f} y={y} {'*' if acc else ' '} {t}")
