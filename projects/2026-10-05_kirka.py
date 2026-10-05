"""Ролик «удар киркой по коже» (test_2.mp4, 23,7 сек).

Запуск: python3 projects/2026-10-05_kirka.py путь/к/test_2.mp4 [папка_вывода]

Исходник: 0–6,77 говорящая голова; 6,77–13,23 кожа на граните, удар в 11,60;
13,23–конец кожа в руке крупно. Тайминги пауз сняты по silencedetect (−38 dB).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
import montage as m  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else "test_2.mp4"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
NAME = "2026-10-05_кирка_v1"

HEAD = (600, 650)     # лицо и верх груди
IMPACT = (590, 930)   # место удара на граните
HAND = (520, 1000)    # кожа в руке

HIT = 11.60           # пик удара в звуке исходника
HIT_F = round(HIT * m.FPS)


def b_roll_zoom(fin):
    """План с ударом: медленный наезд, резкий наезд на ударе, отпускание, тряска."""
    fh = HIT_F - fin

    def z(f, n):
        if f < fh:
            s = 1.0 + 0.05 * m.ease_in_out(f / fh)
        elif f < fh + 4:
            s = 1.05 + 0.09 * m.ease_out((f - fh + 1) / 4)
        elif f < fh + 16:
            s = 1.14 - 0.05 * m.ease_in_out((f - fh - 3) / 12)
        else:
            s = 1.09 + 0.01 * m.ease_in_out((f - fh - 16) / max(1, n - fh - 16))
        dx = dy = 0.0
        g = f - fh
        if 0 <= g < 7:
            amp = 9 * (1 - g / 7)
            ang = [0.3, 2.6, 4.4, 1.2, 3.7, 5.6, 0.9][g]
            dx, dy = amp * m.math.cos(ang), amp * m.math.sin(ang)
        return s, dx, dy
    return z


segs = [
    # говорящая голова: хук уже приближен ×1,10 и наезжает до ×1,14,
    # дальше джамп-каты чередуют крупность
    m.Segment(0.22, 1.12, m.slow_push(1.10, 1.14), HEAD),
    m.Segment(1.45, 4.40, m.slow_push(1.00, 1.05), HEAD),
    m.Segment(4.50, 6.50, m.slow_push(1.08, 1.11), HEAD),
    # смена сцены — растворение
    m.Segment(6.767, 13.00, None, IMPACT, "dissolve"),
    m.Segment(13.45, 16.84, m.slow_push(1.00, 1.05), HAND, "dissolve"),
    m.Segment(17.55, 19.80, m.slow_push(1.08, 1.10), HAND),
    m.Segment(20.25, 21.32, m.slow_push(1.00, 1.04), HAND),
    m.Segment(22.15, 23.40, m.slow_push(1.08, 1.11), HAND),
]
segs[3].zoom = b_roll_zoom(segs[3].fin)
total = m.layout(segs)

hit_out = m.src2out(segs, 3, HIT)
plate_start = segs[3].out_start + m.DISSOLVE
call_from, call_to = round(13.87 * m.FPS), round(15.40 * m.FPS)
call_start = m.src2out(segs, 4, 13.87)
track_src = m.track_point(SRC, call_from, call_to, (550, 1060))
track = {call_start + (k - call_from): xy for k, xy in track_src.items()}

elements = [
    m.Hook(0, "УДАР КИРКОЙ", "по коже", y=800),
    m.Plate(plate_start, "ТЕСТ НА ПРОЧНОСТЬ", dur=66),
    m.Ring(hit_out, IMPACT),
    m.Callout(call_start, call_to - call_from, track, "место удара", "КОЖА НА ГРАНИТЕ",
              label_xy=(600, 470)),
    # Субтитры появятся, когда будет текст речи: m.Subtitles([...])
]

sfx = [("tick", 0), ("tick", plate_start), ("tick", call_start), ("boom", hit_out)]
for s in segs:
    if s.trans_in == "dissolve":
        sfx.append(("rustle", s.out_start - 2))

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, NAME + ".mp4")
m.render(SRC, segs, elements, sfx, out, os.path.join(OUT_DIR, "_work"))

print(f"готово: {out}")
for i, s in enumerate(segs):
    print(f"  план {i + 1}: исходник {s.fin / m.FPS:6.2f}–{s.fout / m.FPS:6.2f} → "
          f"ролик {s.out_start / m.FPS:6.2f}–{(s.out_start + s.length) / m.FPS:6.2f} ({s.trans_in})")
print(f"  удар: {hit_out / m.FPS:.2f} с, плашка: {plate_start / m.FPS:.2f} с, "
      f"выноска: {call_start / m.FPS:.2f} с")
