"""Ролик «картхолдер: новый и год носки» — стиль v2, вставки только чёрные и белые.

Запуск: python3 projects/2026-10-07_cardholder.py папка_с_рабочими_копиями [папка_вывода]
Рабочие копии: IMG_0486.mp4 (вы в кадре), IMG_0494.mp4 (руки + картхолдеры) —
SDR 1080×1920 30 к/с из исходников MOV (HLG HDR, 4K 60).

Структура:
  1. Вы в кадре: «Один из них новый, а вторым я пользуюсь уже больше года» (последний дубль, 40,4 с).
  2. Закадровый голос (дубль 87,9–101,6 с) поверх рук с картхолдерами (IMG_0494).
  3. Снова вы: «Новый — это просто новый, а этот уже мой» (последний дубль, 130,3 с).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402
import kinetic as kn  # noqa: E402
import cutout as co  # noqa: E402
import placement as pl  # noqa: E402
from PIL import Image  # noqa: E402

SRC_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
TALK = os.path.join(SRC_DIR, "IMG_0486.mp4")
HANDS = os.path.join(SRC_DIR, "IMG_0494.mp4")
NAME = "2026-10-07_картхолдер_v2"
FPS = m.FPS

W = json.load(open(os.path.join(HERE, "cardholder.words.json"), encoding="utf-8"))
W["final"]["words"][0]["start"] = 130.28   # распознавание поставило начало дубля, речь с 130,28
W["vo"]["words"][0]["start"] = 88.80       # «Этот» — с 88,8; до него вздох (88,0–88,4), вырезан
W["vo"]["words"][3]["start"] = 90.62       # «я» звучит дважды (89,6 и 90,62) — берём второе, перед «ношу»


def wd(take, word, nth=0):
    hits = [w for w in W[take]["words"] if w["word"].strip(",.!?").lower() == word]
    return hits[nth]


ACCENT = {"больше года", "каждый день", "патиной", "историю", "уже мой"}
TEXT_Y = 960     # по умолчанию центр; для каждого плана высота подбирается (placement.py)


def kf(*keys):
    return m.focus_zoom(m.keyframes(list(keys)), None)


def push(a, b, focus, pull=0.0, n=120):
    return kf((0, a, focus, pull, 1), (0, b, focus, pull, n))


# ---------------------------------------------------------------- план
uzhe = wd("final", "уже")["start"]
f_moi = round(uzhe * FPS) - round(130.15 * FPS)

segs = [
    # 1. вы в кадре; обратный зум в начале: ×1,30 → ×1,00 за ~0,5 с, дальше медленный наезд
    m.Segment(40.42, 43.82, kf((0, 1.30, (540, 900), 0, 1), (0, 1.00, (540, 900), 0, 15),
                               (15, 1.06, (540, 900), 0, 87)), (540, 900)),
    # 2. закадровый голос (звук — IMG_0486, картинка — IMG_0494)
    m.Segment(88.74, 89.56, push(1.05, 1.10, (520, 900)), None, video_in=18.6, video_file=HANDS),
    m.Segment(90.58, 92.12, push(1.10, 1.14, (520, 900)), None, video_in=19.5, video_file=HANDS),
    m.Segment(92.16, 94.36, push(1.00, 1.08, (540, 1000)), None, video_in=40.0, video_file=HANDS),
    m.Segment(94.38, 96.40, push(1.10, 1.22, (560, 900), 0.2), None, video_in=43.0, video_file=HANDS),
    m.Segment(96.46, 97.80, push(1.00, 1.08, (540, 960)), None, video_in=46.2, video_file=HANDS),
    m.Segment(97.84, 99.72, push(1.12, 1.20, (520, 1000)), None, video_in=34.0, video_file=HANDS),
    m.Segment(99.72, 101.66, push(1.00, 1.06, (540, 1000)), None, video_in=52.0, video_file=HANDS),
    # 3. снова вы; наезд на «уже мой»
    m.Segment(130.15, 133.20, kf((0, 1.06, (540, 860), 0, 1), (0, 1.12, (540, 860), 0, f_moi),
                                  (f_moi, 1.32, (560, 560), 0, 6), (f_moi + 6, 1.35, (560, 560), 0, 30)),
              (540, 860)),
]
total = m.layout(segs)


def out_of(t, take_seg=None):
    fr = round(t * FPS)
    for s in segs:
        if s.fin <= fr < s.fout:
            return s.out_start + fr - s.fin
    nxt = [s for s in segs if s.fin > fr]
    return nxt[0].out_start if nxt else total


# ---------------------------------------------------------------- субтитры
# Группы заданы вручную (текст, сколько слов распознавания в неё входит) — так фраза
# режется по смыслу; время каждой группы берётся из распознавания.
SPEC = {
    "intro": [("один из них", 3), ("новый", 1), ("а вторым", 2), ("я пользуюсь", 2),
              ("уже", 1), ("больше года", 2)],
    "vo": [("этот", 1), ("картхолдер", 2), ("я ношу", 2), ("с собой", 2), ("каждый день", 2),
           ("вот что", 2), ("происходит", 1), ("с натуральной", 2), ("кожей", 1),
           ("со временем", 2), ("она покрывается", 2), ("патиной", 1), ("цвет", 1),
           ("становится глубже", 2), ("появляются", 1), ("небольшие следы", 2),
           ("использования", 1), ("и изделие", 2), ("приобретает", 1), ("историю", 1)],
    "final": [("новый", 1), ("это просто", 2), ("новый", 1), ("а этот", 2), ("уже мой", 2)],
}

groups = []
for take, spec in SPEC.items():
    ws = W[take]["words"]
    assert sum(n for _, n in spec) == len(ws), (take, len(ws))
    i = 0
    for text, n in spec:
        part = ws[i:i + n]
        i += n
        a = out_of(part[0]["start"])
        b = out_of(part[-1]["end"]) + 4
        groups.append([a, b, text, text in ACCENT])
groups.sort()
for i in range(len(groups) - 1):
    groups[i][1] = min(groups[i][1], groups[i + 1][0])
groups = [g for g in groups if g[1] - g[0] >= 4]

# ---------------------------------------------------------------- графика


def grab(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", path, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return Image.frombytes("RGB", (m.W, m.H), r.stdout)


# высота текста под каждый план: не закрывать лицо и не закрывать картхолдеры целиком
seg_y = pl.plan_y(segs, TALK, grab, os.path.join(OUT_DIR, "_work", "text_y_cardholder.json"))
# в первом плане картхолдеры в руках на уровне груди (после обратного зума — ниже):
# подбор видит только голову, поэтому текст здесь ставим вручную под картхолдеры
seg_y[0] = 1270


def seg_index(k):
    for i, s in enumerate(segs):
        if s.out_start <= k < s.out_start + s.length:
            last = i
    return last


groups = [tuple(g[:4]) + (seg_y[seg_index(g[0] + 2)],) for g in groups]

cut_vo = segs[1].out_start
cut_final = segs[8].out_start

# v2: карточки с вырезками (коллаж «новый / 1 год» и круг) убраны — только видео, текст и шторки
elements = [
    kn.WipeBar(cut_vo, color=kn.INK),
    kn.WipeBar(cut_final, color=kn.WHITE),
    kn.KineticWords(groups, y=TEXT_Y, accent_color=kn.INK),
]
sfx = [("whoosh", e.start) for e in elements if getattr(e, "sfx", None)]

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
