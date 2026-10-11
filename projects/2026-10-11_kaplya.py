"""Ролик «капни на эту кожу воды» — ответ на комментарий, формат «событие в первом кадре».

Запуск: python3 projects/2026-10-11_kaplya.py папка_с_рабочими_копиями [папка_вывода]
Рабочие копии (папка ch6p): IMG_0507/0508/0509.mp4 — телефон, SDR 1080×1920 30 к/с;
k1809_c / k1809_l / k1812_c .mp4 — вебкамера 1080×720, вырезана вертикаль 405×720 (по центру и слева).

  0:00  вода бьёт в кожу (крупно) + плашка-комментарий «капни на эту кожу воды»
        → лицо: «Меня попросили капнуть воды на кожу, и вот что с ней произойдёт»
        → опрокидываете стакан (вебкамера) — склейка — вода падает на кожу, пятно растекается
        → поднимаете полоску, вода на коже; «ПЯТНО ОСТАНЕТСЯ?»
        → «СПУСТЯ 30 МИН» (IMG_0508) → «СПУСТЯ 1 ЧАС» (IMG_0509) + «ПЯТНА НЕТ»
        → лицо: «Пишите, что проверить следующим».
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402
import kinetic as kn  # noqa: E402

SRC_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
F = {k: os.path.join(SRC_DIR, k + ".mp4") for k in
     ("IMG_0507", "IMG_0508", "IMG_0509", "k1809_c", "k1809_l", "k1812_c")}
NAME = "2026-10-11_капля_v1"
FPS = m.FPS


def kf(*keys):
    return m.focus_zoom(m.keyframes(list(keys)), None)


def push(a, b, focus, pull=0.0, n=90):
    return kf((0, a, focus, pull, 1), (0, b, focus, pull, n))


def seg(src, t0, t1, zoom, center=(540, 960), tr="cut"):
    s = m.Segment(t0, t1, zoom, center, tr, video_file=F[src])
    s.audio_file = F[src]
    return s


HIT = (540, 1300)   # куда падает вода (кадр IMG_0507)
segs = [
    # 0:00 вода бьёт в кожу — крупно, резкий наезд
    seg("IMG_0507", 59.35, 60.55, kf((0, 1.45, HIT, 0.5, 1), (0, 1.32, HIT, 0.5, 20)), HIT),
    # лицо: «Меня попросили капнуть воды на кожу, и вот что с ней произойдёт»
    seg("k1809_c", 13.15, 16.40, kf((0, 1.25, (540, 700), 0, 1), (0, 1.00, (540, 700), 0, 12),
                                    (12, 1.05, (540, 700), 0, 85))),
    # опрокидываете стакан…
    seg("k1809_l", 28.55, 30.25, push(1.00, 1.10, (500, 500), n=50)),
    # …склейка — вода падает на кожу, пятно растекается
    seg("IMG_0507", 59.30, 63.00, kf((0, 1.10, HIT, 0.3, 1), (6, 1.10, HIT, 0.3, 1),
                                     (6, 1.30, HIT, 0.45, 6), (12, 1.36, HIT, 0.45, 90)), HIT),
    # поднимаете полоску — вода стоит на коже
    seg("IMG_0507", 78.90, 80.70, push(1.00, 1.06, (540, 620), n=54)),
    # спустя 30 минут
    seg("IMG_0508", 0.20, 2.60, push(1.04, 1.12, (600, 1250), 0.2, n=72)),
    # спустя час
    seg("IMG_0509", 1.20, 4.40, push(1.00, 1.08, (540, 960), n=96)),
    # лицо: «Пишите, что проверить следующим»
    seg("k1812_c", 15.30, 17.10, push(1.02, 1.08, (540, 700), n=54)),
]
total = m.layout(segs)

# ---------------------------------------------------------------- субтитры (только речь)
def at(i, t):
    s = segs[i]
    return s.out_start + round(t * FPS) - s.fin


subs = [
    (at(1, 13.32), at(1, 13.82), "меня попросили", False),
    (at(1, 13.82), at(1, 14.40), "капнуть воды", True),
    (at(1, 14.40), at(1, 15.02), "на кожу", False),
    (at(1, 15.02), at(1, 15.48), "и вот что", False),
    (at(1, 15.48), segs[1].out_start + segs[1].length, "с ней произойдёт", False),
    (at(7, 15.45), at(7, 15.76), "пишите", False),
    (at(7, 15.76), at(7, 16.28), "что проверить", False),
    (at(7, 16.28), total, "следующим", True),
]
subs = [(a, b, t, acc, 1180) for a, b, t, acc in subs]
# развязка — крупно по центру, на кадре «спустя 1 час»
subs.append((segs[6].out_start + 24, segs[7].out_start, "пятна нет", True, 1480))

# ---------------------------------------------------------------- плашки
TOP = (540, 420)
c_spot = segs[4].out_start
c_30, c_60, c_end = segs[5].out_start, segs[6].out_start, segs[7].out_start
elements = [
    kn.CommentBubble(0, segs[1].out_start + 2, "капни на эту кожу воды", xy=TOP),
    kn.WipeBar(segs[2].out_start, color=kn.INK),
    kn.Chip(c_spot + 2, c_30 - c_spot - 2, "ПЯТНО ОСТАНЕТСЯ?", "dot", xy=TOP),
    kn.Chip(c_30 + 1, c_60 - c_30 - 1, "СПУСТЯ 30 МИН", "clock", xy=TOP),
    kn.Chip(c_60 + 1, c_end - c_60 - 1, "СПУСТЯ 1 ЧАС", "clock", xy=TOP),
    kn.WipeBar(c_end, color=kn.WHITE),
    kn.KineticWords(subs, y=1180, accent_color=kn.INK),
]
sfx = [(e.sfx[0], e.start) for e in elements if getattr(e, "sfx", None)]

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, NAME + ".mp4")
m.render(F["IMG_0507"], segs, elements, sfx, out, os.path.join(OUT_DIR, "_work"))
print(f"готово: {out}, {total / FPS:.2f} с")
for i, s in enumerate(segs):
    print(f"  план {i + 1}: {os.path.basename(s.video_file)} {s.fin / FPS:6.2f}–{s.fout / FPS:6.2f} → "
          f"{s.out_start / FPS:5.2f}–{(s.out_start + s.length) / FPS:5.2f}")
