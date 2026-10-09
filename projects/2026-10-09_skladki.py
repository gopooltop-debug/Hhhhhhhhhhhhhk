"""Ролик «кожа, которая запомнит всё» (складки на пулл-апе) — стиль как у «обложки»
+ чуть больше анимаций: плашка «ЗАГИБ — СЛЕД», счётчик складок, панель «ИСТОРИЯ», плашка «ТВОЯ».

Запуск: python3 projects/2026-10-09_skladki.py папка_с_рабочими_копиями [папка_вывода]
Рабочие копии: IMG_0489.mp4 (вы в кадре), IMG_0492.mp4 (руки сгибают кожу) — SDR 1080×1920 30 к/с.

Структура:
  1. В кадре: «Это кожа, которая запомнит всё» (последний дубль, 19,8 с).
  2. Закадр поверх рук: «Есть кожа, которая после каждого загиба оставляет на себе след. Сначала это просто
     маленькая складка, потом их становится больше. И со временем кожа начинает рассказывать историю того,
     как ты ей пользовался» (дубль 2, 60,9–72,7 с).
  3. В кадре: «Поэтому хорошая кожа не остаётся новой, она становится твоей» (последний дубль, паузы вырезаны).
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
TALK = os.path.join(SRC_DIR, "IMG_0489.mp4")
HANDS = os.path.join(SRC_DIR, "IMG_0492.mp4")
NAME = "2026-10-09_складки_v2"
FPS = m.FPS

RAW = json.load(open(os.path.join(HERE, "video4_raw.words.json"), encoding="utf-8"))["IMG_0489"]


def take(t0, t1, fix=None):
    ws = [dict(w) for w in RAW if t0 <= w["start"] < t1]
    if fix:
        ws[0]["start"] = fix  # распознавание растягивает первое слово дубля; начало — по звуку
    return ws


def W(word, a, b):
    return {"word": word, "start": a, "end": b}


T = {
    "hook": take(19.0, 22.0, 19.80),
    "vo": take(60.0, 73.0, 60.88),
    # финальный дубль: время слов по звуку (распознавание растянуло слова через паузы)
    "fin": [W("поэтому", 90.05, 90.54), W("хорошая", 90.54, 91.0), W("кожа", 91.0, 91.26),
            W("не", 91.26, 91.42), W("остаётся", 91.42, 91.84), W("новой", 91.84, 92.26),
            W("она", 92.8, 92.96), W("становится", 92.96, 93.42), W("твоей", 93.42, 93.9)],
}

SPEC = {
    "hook": [("это кожа", 2), ("которая", 1), ("запомнит всё", 2)],
    "vo": [("есть кожа", 2), ("которая", 1), ("после каждого", 2), ("загиба", 1), ("оставляет", 1),
           ("на себе след", 3), ("сначала это", 2), ("просто", 1), ("маленькая складка", 2),
           ("потом их", 2), ("становится больше", 2), ("и со временем", 3), ("кожа начинает", 2),
           ("рассказывать", 1), ("историю", 1), ("того как", 2), ("ты ей", 2), ("пользовался", 1)],
    "fin": [("поэтому", 1), ("хорошая кожа", 2), ("не остаётся", 2), ("новой", 1),
            ("она становится", 2), ("твоей", 1)],
}
ACCENT = {"запомнит всё", "на себе след", "маленькая складка", "историю", "твоей"}


def kf(*keys):
    return m.focus_zoom(m.keyframes(list(keys)), None)


def push(a, b, focus, pull=0.0, n=120):
    return kf((0, a, focus, pull, 1), (0, b, focus, pull, n))


segs = [
    # 1. в кадре; обратный зум ×1,30 → ×1,00 за 0,5 с
    m.Segment(19.75, 22.00,  # «всё» затихает к 21,95 — без обрезки
              kf((0, 1.30, (540, 900), 0, 1), (0, 1.00, (540, 900), 0, 15),
                               (15, 1.05, (540, 900), 0, 45)), (540, 900)),
    # 2. закадр поверх рук (голос непрерывный, картинка меняется по фразам)
    m.Segment(60.85, 64.08, push(1.00, 1.08, (540, 900)), None, video_in=6.0, video_file=HANDS),
    m.Segment(64.08, 66.48, push(1.10, 1.18, (540, 900)), None, video_in=13.0, video_file=HANDS),
    m.Segment(66.48, 68.12, push(1.00, 1.06, (540, 900)), None, video_in=34.0, video_file=HANDS),
    m.Segment(68.12, 70.58, push(1.06, 1.14, (540, 900)), None, video_in=20.0, video_file=HANDS),
    m.Segment(70.58, 72.75, push(1.00, 1.06, (540, 900)), None, video_in=47.0, video_file=HANDS),
    # 3. в кадре: «поэтому хорошая кожа не остаётся новой» … пауза вырезана … «она становится твоей»
    #    (отдельное «поэтому» с 86,7 с убрано — оно дублировалось)
    m.Segment(90.00, 92.32, push(1.00, 1.04, (540, 900)), (540, 900)),
    m.Segment(92.72, 94.05, kf((0, 1.08, (540, 900), 0, 1), (21, 1.08, (540, 900), 0, 1),
                               (21, 1.22, (560, 640), 0, 6), (27, 1.24, (560, 640), 0, 20)), (540, 900)),
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


seg_y = pl.plan_y(segs, TALK, grab, os.path.join(OUT_DIR, "_work", "text_y_skladki.json"))
for i in (0, 6, 7):  # в кадре кожа в руках на уровне груди — текст под ней
    seg_y[i] = max(seg_y[i], 1150)


def seg_index(k):
    last = 0
    for i, s in enumerate(segs):
        if s.out_start <= k < s.out_start + s.length:
            last = i
    return last


groups = [tuple(g[:4]) + (seg_y[seg_index(g[0] + 2)],) for g in groups]

# ---------------------------------------------------------------- анимации
cut_vo, cut_fin = segs[1].out_start, segs[6].out_start
f_zagib = out_of(wstart("vo", "загиба"))
f_sklad = out_of(wstart("vo", "маленькая"))
f_bolshe = out_of(wstart("vo", "становится"))
f_vrem = out_of(wstart("vo", "со"))
f_tvoei = out_of(wstart("fin", "твоей"))
TOP = (540, 420)

counter_steps = [(f_sklad, 1)] + [(f_bolshe + 3 * i, v) for i, v in enumerate((2, 3, 5, 8, 12), 1)]
elements = [
    kn.WipeBar(cut_vo, color=kn.INK),
    kn.WipeBar(cut_fin, color=kn.WHITE),
    # «…после каждого загиба оставляет на себе след»
    kn.Chip(f_zagib, segs[2].out_start - 2 - f_zagib, "ЗАГИБ — СЛЕД", "fold", xy=TOP),
    # «маленькая складка» — 1; «потом их становится больше» — цифры щёлкают до 12
    kn.CounterChip(f_sklad, segs[4].out_start - 2 - f_sklad, "СКЛАДКИ", counter_steps, "fold", xy=TOP),
    # «и со временем… историю того, как ты ей пользовался»
    kn.ProgressPanel(f_vrem, cut_fin - 3 - f_vrem, "ИСТОРИЯ", "clock", xy=TOP, width=680,
                     fill_from=f_vrem + 6, fill_to=cut_fin - 10, values=["1 МЕС", "6 МЕС", "1 ГОД"]),
    # «она становится твоей»
    kn.Chip(f_tvoei, total + 10 - f_tvoei, "ТВОЯ", "check", xy=(540, 1330), dark=True),
    kn.KineticWords(groups, y=960, accent_color=kn.INK),
]
sfx = [(e.sfx[0], e.start) for e in elements if getattr(e, "sfx", None)]
sfx += [("pop", k) for k, _ in counter_steps[1:]]

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
