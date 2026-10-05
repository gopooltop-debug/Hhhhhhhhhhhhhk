"""Ролик «удар киркой по коже конкурента» (test_2.mp4, 23,7 сек).

Запуск: python3 projects/2026-10-05_kirka.py путь/к/test_2.mp4 [папка_вывода]

Исходник: 0–6,77 говорящая голова; 6,77–13,23 кожа на граните, удар в 11,60;
13,23–конец кожа в руке крупно. Тайминги пауз сняты по silencedetect (−38 dB),
тайминги слов — вручную по спектрограмме (распознавания речи в среде нет).

Текст: «Сегодня мы сравним нашу кожу с кожей конкурента и посмотрим, какая из них
лучше. И вообще она какая-то некачественная, шов мне не нравится, сейчас мы посмотрим.
Как видите, кожа конкурента сразу деформировалась, появилась довольно таки большая
царапина, вмятина».

v2: зумы крупнее (до ×1,40, по заданию: больше, чем ×1,16 из стиля), больше моушна.
v4: на базе v2; исправлен текст после «конкурента» («и посмотрим, какая из них лучше»),
тайминги слов выверены по спектрограмме (шипящие и смычки), на ударе графики нет.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
import montage as m  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else "test_2.mp4"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "output"
NAME = "2026-10-05_кирка_v4"
FPS = m.FPS

HEAD = (600, 650)     # лицо и верх груди
FACE = (620, 380)     # лицо
IMPACT = (590, 930)   # место удара на граните
HIT = 11.60           # пик удара в звуке исходника
HIT_F = round(HIT * FPS)

# ---------------------------------------------------------------- слова
# (начало в исходнике, слово/группа, акцент). Группы по 1–2 слова.
WORDS = [
    (0.27, "Сегодня", False),
    (0.91, "мы", False),
    (1.73, "сравним", False),
    (2.48, "нашу кожу", False),
    (2.98, "с кожей", False),
    (3.49, "конкурента", True),
    (4.57, "и посмотрим", False),
    (5.27, "какая из них", False),
    (5.82, "лучше", False),
    (6.76, "и вообще", False),
    (7.27, "она какая-то", False),
    (7.72, "некачественная", False),
    (8.45, "шов", True),
    (8.80, "мне не нравится", False),
    (9.95, "сейчас мы", False),
    (10.40, "посмотрим", False),
    (13.69, "как видите", False),
    (14.45, "кожа конкурента", False),
    (15.53, "сразу", False),
    (16.07, "деформировалась", True),
    (17.70, "появилась", False),
    (18.45, "довольно таки", False),
    (19.25, "большая", False),
    (20.35, "царапина", False),
    (22.25, "вмятина", True),
]
# концы фраз: после них субтитр гаснет, а не висит над паузой
PHRASE_ENDS = [1.08, 4.22, 6.20, 9.50, 10.90, 16.75, 19.72, 21.26, 23.40]


def W_(text):
    return next(t for t, w, _ in WORDS if w == text)


# ---------------------------------------------------------------- трекинг вмятины
TRACK_FROM, TRACK_TO = round(13.87 * FPS), round(23.40 * FPS)
track_src = m.track_point(SRC, TRACK_FROM, TRACK_TO, (550, 1060))


def dent_at(fr, window=21):
    """Сглаженная позиция вмятины для камеры (кадр исходника)."""
    xs, ys, n = 0.0, 0.0, 0
    for q in range(fr - window // 2, fr + window // 2 + 1):
        q = min(max(q, TRACK_FROM), TRACK_TO)
        if q in track_src:
            xs += track_src[q][0]; ys += track_src[q][1]; n += 1
    return (xs / n, ys / n)


# ---------------------------------------------------------------- зумы
def f_of(seg_in, t):
    return round(t * FPS) - round(seg_in * FPS)


def head_hook():
    return m.focus_zoom(m.keyframes([(0, 1.15, HEAD, 0, 1), (0, 1.22, HEAD, 0, 27)]), None)


def head_main(fin_t):
    fk = f_of(fin_t, W_("конкурента"))
    return m.focus_zoom(m.keyframes([
        (0, 1.00, HEAD, 0, 1),
        (0, 1.08, HEAD, 0, fk),
        (fk, 1.40, FACE, 0.0, 9),          # крупный наезд на «конкурента»
        (fk + 9, 1.43, FACE, 0.0, 40),
    ]), None)


def head_tail():
    return m.focus_zoom(m.keyframes([(0, 1.06, (600, 600), 0, 1), (0, 1.16, (600, 600), 0, 60)]), None)


def broll(fin_t):
    fs = f_of(fin_t, W_("шов"))
    fp = f_of(fin_t, W_("сейчас мы")) - 6
    fq = f_of(fin_t, 10.95)
    fh = HIT_F - round(fin_t * FPS)
    keys = m.keyframes([
        (0, 1.00, (420, 1100), 0, 1),
        (0, 1.10, (380, 1110), 0.1, fs),
        (fs - 3, 1.32, (360, 1120), 0.35, 10),     # «шов» — крупно на кожу
        (fs + 7, 1.36, (370, 1130), 0.35, 40),
        (fp, 1.00, (450, 1200), 0, 14),           # «сейчас мы посмотрим» — отъезд
        (fq, 1.12, IMPACT, 0.3, fh - fq),          # тишина перед ударом — наезд
        (fh, 1.40, IMPACT, 0.45, 4),               # удар
        (fh + 4, 1.25, IMPACT, 0.4, 16),
        (fh + 20, 1.28, IMPACT, 0.4, 40),
    ])

    def shake(f):
        g = f - fh
        if 0 <= g < 8:
            amp = 14 * (1 - g / 8)
            ang = [0.3, 2.6, 4.4, 1.2, 3.7, 5.6, 0.9, 3.0][g]
            return amp * m.math.cos(ang), amp * m.math.sin(ang)
        return 0, 0
    return m.focus_zoom(keys, None, shake)


def dent_zoom(fin_t, keys):
    fin = round(fin_t * FPS)
    kf = m.keyframes(keys)
    return m.focus_zoom(kf, lambda f: dent_at(fin + f))


segs = [
    m.Segment(0.22, 1.12, head_hook(), HEAD),
    m.Segment(1.45, 4.40, head_main(1.45), HEAD),
    m.Segment(4.50, 6.50, head_tail(), HEAD),
    m.Segment(6.767, 13.00, broll(6.767), IMPACT, "dissolve"),
    m.Segment(13.45, 16.84, None, None, "dissolve"),
    m.Segment(17.55, 19.80, None, None),
    m.Segment(20.25, 21.32, m.focus_zoom(m.keyframes(
        [(0, 1.00, (540, 1000), 0, 1), (0, 1.12, (540, 1000), 0, 32)]), None), (540, 1000)),
    m.Segment(22.15, 23.40, None, None),
]
fd = f_of(13.45, W_("деформировалась"))
segs[4].zoom = dent_zoom(13.45, [
    (0, 1.00, (0, 0), 0.0, 1),
    (0, 1.12, (0, 0), 0.3, fd),
    (fd, 1.35, (0, 0), 0.6, 9),                    # «деформировалась»
    (fd + 9, 1.38, (0, 0), 0.6, 30),
])
segs[5].zoom = dent_zoom(17.55, [(0, 1.18, (0, 0), 0.4, 1), (0, 1.26, (0, 0), 0.5, 67)])
segs[7].zoom = dent_zoom(22.15, [(0, 1.15, (0, 0), 0.3, 1), (3, 1.38, (0, 0), 0.65, 20),
                                  (23, 1.40, (0, 0), 0.65, 15)])
total = m.layout(segs)


def seg_of(t):
    fr = round(t * FPS)
    for i, s in enumerate(segs):
        if s.fin <= fr < s.fout:
            return i
    # слово начинается чуть до обрезки — ближайший отрезок справа
    return min(range(len(segs)), key=lambda i: abs(segs[i].fin - fr))


def out_of(t):
    i = seg_of(t)
    s = segs[i]
    fr = min(max(round(t * FPS), s.fin), s.fout - 1)
    return s.out_start + fr - s.fin


# ---------------------------------------------------------------- субтитры
HOOK_END = 75
subs = []
for j, (t, text, acc) in enumerate(WORDS):
    a = out_of(t)
    end_src = min(e for e in PHRASE_ENDS if e > t)
    b = out_of(end_src) + 6
    if j + 1 < len(WORDS):
        b = min(b, out_of(WORDS[j + 1][0]))
    b = min(b, total)
    if a < HOOK_END:  # пока висит хук, субтитров нет
        if b - HOOK_END < 8:
            continue
        a = HOOK_END  # слово ещё звучит, когда хук ушёл, — показываем его с этого кадра
    subs.append((a, b, text, acc))
underline = next(i for i, w in enumerate(subs) if w[2] == "вмятина")

# ---------------------------------------------------------------- графика
hit_out = out_of(HIT)
f_better = out_of(W_("какая из них"))
f_vs_end = out_of(6.20) + 3
f_list = out_of(6.80)
f_kach = out_of(W_("некачественная"))
f_chest = out_of(7.95)  # «ч» в «некачественная» — тут ставим крестик
f_shov = out_of(W_("шов"))
f_look = out_of(W_("сейчас мы"))
call_start = out_of(13.87)
call_end = out_of(15.45)
f_deform = out_of(W_("деформировалась"))
f_sum = segs[5].out_start
f_scr = out_of(W_("царапина"))
f_vm = out_of(W_("вмятина"))

track_out = {}
for k, xy in track_src.items():
    t = k / FPS
    i = seg_of(t)
    if segs[i].fin <= k < segs[i].fout:
        track_out[segs[i].out_start + k - segs[i].fin] = xy

elements = [
    m.Hook(0, "СРАВНИМ НАШУ КОЖУ", "с конкурентом", y=800),
    # «НАША vs КОНКУРЕНТ» держится и на «и посмотрим, какая из них лучше»:
    # линия-указатель переезжает между сторонами
    m.Versus(HOOK_END + 2, f_vs_end - HOOK_END - 2, "НАША", "КОНКУРЕНТ", y=1010,
             picks=[(f_better, "l"), (f_better + 9, "r"), (out_of(W_("лучше")), "l")]),
    m.Checklist(f_list, out_of(9.62) - f_list, "КОЖА КОНКУРЕНТА",
                [("качество", f_kach - 4, f_chest), ("шов", f_shov - 2, f_shov + 6)]),
    m.Plate(f_look, "ТЕСТ НА ПРОЧНОСТЬ", dur=hit_out - f_look - 2),
    # на ударе графики нет: только наезд, тряска и низкий удар в звуке
    m.Callout(call_start, call_end - call_start, track_out, "вмятина", "КОЖА КОНКУРЕНТА",
              label_xy=(600, 470)),
    m.DrawCircle(f_deform, segs[4].out_start + segs[4].length - f_deform, track_out, radius=110),
    # последние элементы не гаснут: ролик обрывается на мысли
    m.Checklist(f_sum, total - f_sum + 10, "КОЖА КОНКУРЕНТА",
                [("качество", f_sum, f_sum - 20), ("шов", f_sum + 3, f_sum - 20),
                 ("держит удар", f_scr - 10, f_scr)]),
    m.DrawCircle(f_vm, total - f_vm + 10, track_out, radius=100),
    m.Subtitles(subs, underline_word=underline),
]

sfx = [("tick", e.start) for e in elements if getattr(e, "sfx", None)]
sfx += [("tick", f_chest), ("tick", f_shov + 6), ("tick", f_scr), ("boom", hit_out)]
for s in segs:
    if s.trans_in == "dissolve":
        sfx.append(("rustle", s.out_start - 2))

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, NAME + ".mp4")
m.render(SRC, segs, elements, sfx, out, os.path.join(OUT_DIR, "_work"))

print(f"готово: {out}")
for i, s in enumerate(segs):
    print(f"  план {i + 1}: исходник {s.fin / FPS:6.2f}–{s.fout / FPS:6.2f} → "
          f"ролик {s.out_start / FPS:6.2f}–{(s.out_start + s.length) / FPS:6.2f} ({s.trans_in})")
for a, b, text, acc in subs:
    print(f"  {a / FPS:6.2f}–{b / FPS:6.2f} {'*' if acc else ' '} {text}")
