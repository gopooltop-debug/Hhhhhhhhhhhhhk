"""«Кирка» v5 — новая стилистика (style/montage-style-v2.md): кинетический текст по центру,
шторки, цветная карточка, коллажи из вырезок, живое видео — основа.

Запуск: python3 projects/2026-10-05_kirka_v5.py путь/к/test_2.mp4 [папка_вывода]
Субтитры — из projects/2026-10-05_kirka.words.json (engine/transcribe.py).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
import montage as m  # noqa: E402
import kinetic as kn  # noqa: E402
import cutout as co  # noqa: E402
from PIL import Image  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else "test_2.mp4"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
NAME = "2026-10-05_кирка_v5"
FPS = m.FPS

HEAD = (600, 650)
FACE = (620, 380)
IMPACT = (590, 930)
HIT = 11.60
HIT_F = round(HIT * FPS)

words = json.load(open(os.path.join(HERE, "2026-10-05_kirka.words.json"), encoding="utf-8"))
SUBS = words["subtitles"]
FIX = {"конкурентов": "конкурента"}          # правки распознавания
ACCENT = {"конкурента", "шов", "деформировалась", "большая вмятина"}


def ws(text):
    """Начало слова (по распознаванию), сек исходника."""
    for w in words["words"]:
        if w["word"].strip(",.!?").lower() == text:
            return w["start"]
    raise KeyError(text)


# ---------------------------------------------------------------- трекинг вмятины
TR_A, TR_B = round(13.87 * FPS), round(23.40 * FPS)
track = m.track_point(SRC, TR_A, TR_B, (550, 1060))


def dent(fr, win=21):
    xs = ys = n = 0
    for q in range(fr - win // 2, fr + win // 2 + 1):
        q = min(max(q, TR_A), TR_B)
        if q in track:
            xs += track[q][0]; ys += track[q][1]; n += 1
    return (xs / n, ys / n)


def fo(t_in, t):
    return round(t * FPS) - round(t_in * FPS)


def kf(*keys):
    return m.focus_zoom(m.keyframes(list(keys)), None)


def dent_zoom(video_in, *keys):
    vin = round(video_in * FPS)
    return m.focus_zoom(m.keyframes(list(keys)), lambda f: dent(vin + f))


# ---------------------------------------------------------------- план
t_konk = ws("конкурентов")
head = kf((0, 1.12, HEAD, 0, 1), (0, 1.18, HEAD, 0, 60),
          (fo(1.62, t_konk), 1.36, FACE, 0, 6), (fo(1.62, t_konk) + 6, 1.40, FACE, 0, 30))

broll_a = kf((0, 1.05, (380, 1110), 0.15, 1), (0, 1.12, (380, 1110), 0.2, 20),
             (fo(6.80, ws("шов")), 1.38, (360, 1120), 0.4, 6),
             (fo(6.80, ws("шов")) + 6, 1.42, (370, 1130), 0.4, 30))
broll_b = kf((0, 1.00, (450, 1200), 0, 1), (0, 1.10, (480, 1220), 0.1, 38))

fh = HIT_F - round(11.25 * FPS)


def hit_zoom():
    keys = m.keyframes([(0, 1.10, IMPACT, 0.3, 1), (0, 1.14, IMPACT, 0.3, fh),
                        (fh, 1.42, IMPACT, 0.45, 4), (fh + 4, 1.26, IMPACT, 0.4, 14),
                        (fh + 18, 1.28, IMPACT, 0.4, 30)])

    def shake(f):
        g = f - fh
        if 0 <= g < 8:
            amp = 16 * (1 - g / 8)
            ang = [0.3, 2.6, 4.4, 1.2, 3.7, 5.6, 0.9, 3.0][g]
            return amp * m.math.cos(ang), amp * m.math.sin(ang)
        return 0, 0
    return m.focus_zoom(keys, None, shake)


fd = fo(13.55, ws("деформировалась"))
segs = [
    m.Segment(1.62, 6.15, head, HEAD),                              # «Сегодня … лучше»
    m.Segment(6.80, 9.47, broll_a, (380, 1110)),                    # «и вообще … нравится»
    m.Segment(9.66, 10.92, broll_b, (450, 1200)),                   # «и сейчас мы посмотрим»
    m.Segment(11.25, 12.40, hit_zoom(), IMPACT),                    # удар, без графики
    m.Segment(13.55, 16.80, dent_zoom(13.55, (0, 1.0, (0, 0), 0, 1), (0, 1.12, (0, 0), 0.3, fd),
                                      (fd, 1.36, (0, 0), 0.6, 6), (fd + 6, 1.40, (0, 0), 0.6, 30)),
              None),                                                # «как видите … деформировалась»
    m.Segment(17.83, 19.72, dent_zoom(17.83, (0, 1.16, (0, 0), 0.4, 1), (0, 1.24, (0, 0), 0.5, 56)),
              None),                                                # «появилась … большая царапина»
    # «большая вмятина»: звук 20.30–21.60, картинка — вмятина крупно (22.15…)
    m.Segment(20.30, 21.60, dent_zoom(22.15, (0, 1.20, (0, 0), 0.5, 1), (0, 1.40, (0, 0), 0.7, 14),
                                      (14, 1.43, (0, 0), 0.7, 25)), None, video_in=22.15),
]
total = m.layout(segs)


def out_of(t, clamp=True):
    fr = round(t * FPS)
    for s in segs:
        if s.fin <= fr < s.fout:
            return s.out_start + fr - s.fin
    nxt = [s for s in segs if s.fin > fr]
    return nxt[0].out_start if nxt else total


# ---------------------------------------------------------------- субтитры
groups = []
for i, g in enumerate(SUBS):
    text = " ".join(FIX.get(w, w) for w in g["text"].split())
    if text == "то есть":
        continue
    fr = round(g["start"] * FPS)
    if not any(s.fin - 3 <= fr < s.fout for s in segs):
        continue
    a = out_of(g["start"])
    b = out_of(g["end"]) + 4
    groups.append([a, b, text, text in ACCENT])
groups.sort()
# слишком короткие группы (< 0,2 с) склеиваем со следующей (без акцентов, до 3 слов)
i = 0
while i < len(groups) - 1:
    short = min(groups[i][1], groups[i + 1][0]) - groups[i][0] < 6
    words_n = len(groups[i][2].split()) + len(groups[i + 1][2].split())
    if (short and not groups[i][3] and not groups[i + 1][3] and words_n <= 3
            and groups[i + 1][0] - groups[i][1] <= 6):
        a, _, t, acc = groups[i]
        _, b2, t2, acc2 = groups.pop(i + 1)
        groups[i] = [a, b2, f"{t} {t2}", acc or acc2]
    else:
        i += 1
for i in range(len(groups) - 1):
    groups[i][1] = min(groups[i][1], groups[i + 1][0])
groups = [tuple(g) for g in groups if g[1] - g[0] >= 4]

# ---------------------------------------------------------------- графика
cut1 = segs[1].out_start          # говорящая голова → кожа
cut2 = segs[4].out_start          # удар → крупно
f_which = out_of(ws("какая"))
f_better_end = out_of(6.10)
f_bad = out_of(ws("некачественная"))
f_bad_end = out_of(8.34)
f_scr = out_of(ws("большая"))      # первое «большая» — «большая царапина»
f_scr_end = segs[5].out_start + segs[5].length

def grab(t):
    import subprocess
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", SRC, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return Image.frombytes("RGB", (m.W, m.H), r.stdout)


CACHE = os.path.join(OUT_DIR, "_work", "cutouts")
person = co.cached(os.path.join(CACHE, "person_3.0.png"), lambda: co.collage_style(co.cutout(grab(3.0))))
leather = co.cached(os.path.join(CACHE, "leather_14.3.png"),
                    lambda: co.collage_style(co.cutout(grab(14.3))))
co.release()

cards = [
    # «какая из них лучше» — коллаж: вы в бордовом круге
    # держится до шторки: склейка на кожу уходит под неё
    kn.CollageCard(f_which, cut1 + 1 - f_which, person, circle=kn.BORDO, cy=700, cut_h=880, exit_=1),
    # «некачественная» — бордовая карточка во весь экран
    kn.ColorCard(f_bad, f_bad_end - f_bad, color=kn.BORDO),
    # «большая царапина» — коллаж: кожа конкурента в коричневом круге
    kn.CollageCard(f_scr, f_scr_end - f_scr, leather, circle=kn.BROWN, cy=720, cut_h=640,
                   circle_r=330),
]
# тёмный текст — пока под ним светлая карточка; на шторке и видео — белый
light = [(c.start, min(c.start + c.dur, cut1 - 2) if c.start < cut1 else c.start + c.dur)
         for c in cards if isinstance(c, kn.CollageCard)]
elements = cards + [
    kn.WipeBar(cut1, color=kn.BORDO),
    kn.WipeBar(cut2, color=kn.BROWN),
    kn.KineticWords(groups, light=light),
]

sfx = [("whoosh", e.start) for e in elements if getattr(e, "sfx", None)]
sfx.append(("boom", out_of(HIT)))

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, NAME + ".mp4")
m.render(SRC, segs, elements, sfx, out, os.path.join(OUT_DIR, "_work"))

print(f"готово: {out}")
for i, s in enumerate(segs):
    print(f"  план {i + 1}: звук {s.fin / FPS:6.2f}–{s.fout / FPS:6.2f} → "
          f"ролик {s.out_start / FPS:6.2f}–{(s.out_start + s.length) / FPS:6.2f}")
for a, b, t, acc in groups:
    print(f"  {a / FPS:6.2f}–{b / FPS:6.2f} {'*' if acc else ' '} {t}")
