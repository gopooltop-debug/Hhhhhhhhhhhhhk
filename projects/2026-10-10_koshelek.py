"""Ролик «кошелёк: сколько часов ушло» — стиль как у «складок».

Запуск: python3 projects/2026-10-10_koshelek.py папка_с_рабочей_копией [папка_вывода]
Рабочая копия: src.mp4 — смонтированный автором «1010 (1).mp4», приведённый к 1080×1920.

Структура исходника (уже подредактирован автором):
  0,6–4,4   «На это изделие уже ушло столько часов, а оно ещё даже не готово»
  6,5–12,5  «Изделие уже почти готово. Остаётся обработать края, всё подровнять и проверить каждую деталь»
  13,7–15,6 «А потратили мы уже столько часов» — показываете рукой на кошелёк → анимация «?»
  16,9–конец руки с кошельком без речи; на раскрытии (~28,5 с) — ответ «6 ЧАСОВ» сразу целиком.
Тишина между фразами (2 с и 1,2 с) вырезана.
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
SRC = os.path.join(SRC_DIR, "src.mp4")
NAME = "2026-10-10_кошелёк_v1"
FPS = m.FPS

RAW = json.load(open(os.path.join(HERE, "video5_raw.words.json"), encoding="utf-8"))
WORDS = [dict(w) for w in RAW if w["start"] < 16]   # «Субтитры делал…» на 38 с — ошибка распознавания
WORDS[0]["start"] = 0.60                               # «На» — с 0,6 по звуку


def part(t0, t1):
    return [w for w in WORDS if t0 <= w["start"] < t1]


T = {"a": part(0, 5), "b": part(6, 13), "c": part(13, 16)}
SPEC = {
    "a": [("на это изделие", 3), ("уже ушло", 2), ("столько часов", 2), ("а оно ещё", 3),
          ("даже не готово", 3)],
    "b": [("изделие", 1), ("уже почти готово", 3), ("остаётся", 1), ("обработать края", 2),
          ("всё подровнять", 2), ("и проверить", 2), ("каждую деталь", 2)],
    "c": [("а потратили", 2), ("мы уже", 2), ("столько часов", 2)],
}
ACCENT = {"столько часов", "даже не готово", "каждую деталь"}


def kf(*keys):
    return m.focus_zoom(m.keyframes(list(keys)), None)


def push(a, b, focus, pull=0.0, n=150):
    return kf((0, a, focus, pull, 1), (0, b, focus, pull, n))


f_q = round(14.85 * FPS) - round(13.40 * FPS)   # «столько» в плане 3
segs = [
    # в кадре; обратный зум ×1,30 → ×1,00 за 0,5 с
    m.Segment(0.52, 4.62, kf((0, 1.30, (540, 900), 0, 1), (0, 1.00, (540, 900), 0, 15),
                             (15, 1.05, (540, 900), 0, 105)), (540, 900)),
    m.Segment(6.30, 12.60, push(1.00, 1.06, (600, 700)), (600, 700)),
    # «а потратили мы уже столько часов» — на «столько» лёгкий наезд к кошельку и «?»
    m.Segment(13.40, 16.87, kf((0, 1.00, (540, 900), 0, 1), (0, 1.03, (540, 900), 0, f_q),
                               (f_q, 1.12, (420, 800), 0, 8), (f_q + 8, 1.14, (420, 800), 0, 40)),
              (540, 900)),
    # руки с кошельком (без речи), монтаж автора сохранён
    m.Segment(16.87, 28.40, push(1.00, 1.05, (540, 960)), (540, 960)),
    # раскрытие — «6 ЧАСОВ»
    m.Segment(28.40, 33.40, kf((0, 1.00, (540, 960), 0, 1), (0, 1.10, (540, 1000), 0, 20),
                               (20, 1.12, (540, 1000), 0, 130)), (540, 1000)),
    m.Segment(33.40, 53.70, push(1.00, 1.06, (540, 960), n=600), (540, 960)),
]
total = m.layout(segs)


def out_of(t):
    fr = round(t * FPS)
    for s in segs:
        if s.fin <= fr < s.fout:
            return s.out_start + fr - s.fin
    nxt = [s for s in segs if s.fin > fr]
    return nxt[0].out_start if nxt else total


groups = []
for key, spec in SPEC.items():
    ws = T[key]
    assert sum(n for _, n in spec) == len(ws), (key, [w["word"] for w in ws])
    i = 0
    for text, n in spec:
        p = ws[i:i + n]
        i += n
        groups.append([out_of(p[0]["start"]), out_of(p[-1]["end"]) + 4, text, text in ACCENT])
groups.sort()
for i in range(len(groups) - 1):
    groups[i][1] = min(groups[i][1], groups[i + 1][0])
groups = [g for g in groups if g[1] - g[0] >= 4]


def grab(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", path, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return Image.frombytes("RGB", (m.W, m.H), r.stdout)


talk = segs[:3]
seg_y = pl.plan_y(talk, SRC, grab, os.path.join(OUT_DIR, "_work", "text_y_koshelek.json"))
seg_y[0] = max(seg_y[0], 1150)   # кошелёк в руках на уровне груди — текст под ним
seg_y[2] = max(seg_y[2], 1150)


def seg_index(k):
    last = 0
    for i, s in enumerate(segs):
        if s.out_start <= k < s.out_start + s.length:
            last = i
    return last


groups = [tuple(g[:4]) + (seg_y.get(seg_index(g[0] + 2), 1150),) for g in groups]

cut_b = segs[3].out_start
f_open = segs[4].out_start
# раскрытие интриги: «6 ЧАСОВ» сразу целиком, без поэтапного набегания часов
stat = kn.TimeStat(f_open + 3, segs[4].length + 20, 6, xy=(540, 400), count=False)
elements = [
    kn.WipeBar(cut_b, color=kn.INK),
    # «столько часов»: «?» над кошельком, куда вы показываете (координаты исходника)
    kn.QuestionMark(out_of(14.85), cut_b - out_of(14.85) + 2, (290, 500), r=125),
    # раскрываете кошелёк — ответ
    stat,
    kn.KineticWords(groups, y=960, accent_color=kn.INK),
]
sfx = [(e.sfx[0], e.start) for e in elements if getattr(e, "sfx", None)]
sfx += [("pop", k) for k in stat.tick_frames()]

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, NAME + ".mp4")
m.render(SRC, segs, elements, sfx, out, os.path.join(OUT_DIR, "_work"))

print(f"готово: {out}")
for i, s in enumerate(segs):
    print(f"  план {i + 1}: {s.fin / FPS:6.2f}–{s.fout / FPS:6.2f} → "
          f"ролик {s.out_start / FPS:6.2f}–{(s.out_start + s.length) / FPS:6.2f}")
print("  «?» с", round(out_of(14.85) / FPS, 2), " «6 ЧАСОВ» с", round(stat.start / FPS, 2))
for a, b, t, acc, y in groups:
    print(f"  {a / FPS:6.2f}–{b / FPS:6.2f} y={y} {'*' if acc else ' '} {t}")
