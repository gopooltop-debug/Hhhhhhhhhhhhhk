"""Стиль v2 («кинетика»): слова по центру с переворотом и размытием, линия под фразой,
бордовая плашка под акцентом, цветные карточки, карточки-коллажи, шторки.

Палитра: белый, чёрный, коричневый, бордовый. Шрифт: Montserrat 900/800.
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import montage as m
from montage import W, H, Element, clamp01, ease_out, ease_in_out, text_image

WHITE = (0xF6, 0xF4, 0xF1)
INK = (0x16, 0x15, 0x14)
BROWN = (0x6B, 0x4F, 0x3A)
BORDO = (0x75, 0x40, 0x43)
LIGHT_GRAY = (0xE4, 0xE1, 0xDC)

CENTER_Y = 1000  # центр текста: середина кадра, чуть ниже лица в говорящей голове
MAX_W = 900


# ---------------------------------------------------------------- геометрия

def flip(img, angle, blur):
    """Поворот RGBA-картинки вокруг горизонтальной оси (angle, рад) + вертикальное размытие."""
    w, h = img.size
    pad_x, pad_y = int(w * 0.25), int(h * 0.9)
    cw, ch = w + 2 * pad_x, h + 2 * pad_y
    f = 1400.0
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = []
    for (x, y) in src:
        X, Y = x - w / 2, y - h / 2
        y3, z3 = Y * math.cos(angle), Y * math.sin(angle)
        k = f / (f + z3)
        dst.append([cw / 2 + X * k, ch / 2 + y3 * k])
    M = cv2.getPerspectiveTransform(src, np.float32(dst))
    arr = np.asarray(img)
    # premultiplied alpha, чтобы размытие не давало тёмных ореолов
    a = arr[..., 3:4].astype(np.float32) / 255
    pm = np.concatenate([arr[..., :3] * a, a * 255], axis=2).astype(np.float32)
    out = cv2.warpPerspective(pm, M, (cw, ch), flags=cv2.INTER_LINEAR, borderValue=0)
    b = int(round(blur))
    if b >= 2:
        out = cv2.blur(out, (max(1, b // 3), b))
    alpha = out[..., 3:4]
    rgb = np.where(alpha > 0, out[..., :3] / np.maximum(alpha / 255, 1e-3), 0)
    res = np.concatenate([np.clip(rgb, 0, 255), np.clip(alpha, 0, 255)], axis=2).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def paste_center(layer, img, cx, cy, alpha=1.0):
    if alpha <= 0:
        return
    if alpha < 1:
        a = np.asarray(img.getchannel("A"), np.float32) * alpha
        img = img.copy()
        img.putalpha(Image.fromarray(a.astype(np.uint8)))
    x, y = int(round(cx - img.width / 2)), int(round(cy - img.height / 2))
    layer.alpha_composite(img, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))


# ---------------------------------------------------------------- слова по центру

SHORT = {"и", "а", "в", "во", "с", "со", "к", "ко", "у", "о", "об", "из", "на", "не", "ни",
         "мы", "мне", "же", "ли", "бы", "то", "по", "за", "от", "до", "что", "как"}


def split_group(text):
    """«и посмотрим» → ('и', 'посмотрим'): короткие слова в начале идут маленькой приставкой."""
    words = text.split()
    pre = []
    while len(words) > 1 and words[0] in SHORT:
        pre.append(words.pop(0))
    return " ".join(pre), " ".join(words)


class KineticWords(Element):
    """Субтитры по центру: группа влетает снизу с переворотом и размытием (6 кадров),
    уходит вверх (4 кадра). Приставка — мелко над главным словом. Под фразой тонкая линия.

    groups: [(кадр_начала, кадр_конца, текст, акцент)] — кадры ролика.
    light: [(с, по)] — кадры, где под текстом светлая карточка (текст тёмный).
    """
    shadow_kw = {"radius": 14, "opacity": 0.5}

    def __init__(self, groups, light=(), size=128, y=CENTER_Y, light_y=1230, accent_color=BORDO):
        self.groups = sorted(groups, key=lambda g: g[0])
        self.light = list(light)
        self.size, self.base_y, self.light_y = size, y, light_y
        self.accent_color = accent_color
        self.start = self.groups[0][0]
        self.dur = self.groups[-1][1] + 6 - self.start
        # фразы для линии: группы, идущие подряд без паузы
        self.phrases = []
        for g in self.groups:
            if self.phrases and g[0] - self.phrases[-1][1] <= 3:
                self.phrases[-1][1] = g[1]
            else:
                self.phrases.append([g[0], g[1]])

    def _is_light(self, k):
        return any(a <= k < b for a, b in self.light)

    def _block(self, text, accent, color, wipe):
        pre, main = split_group(text)
        mi = text_image(main.upper(), "mont900", self.size, color, spacing=-2)
        if mi.width > MAX_W:
            mi = mi.resize((MAX_W, int(mi.height * MAX_W / mi.width)), Image.LANCZOS)
        pi = text_image(pre.upper(), "mont800", int(self.size * 0.36), color, spacing=3) if pre else None
        padx, pady = 26, 12
        bw = mi.width + 2 * padx
        bh = mi.height + 2 * pady + (pi.height + 4 if pi else 0)
        blk = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        top = 0
        if pi:
            blk.alpha_composite(pi, ((bw - pi.width) // 2, 0))
            top = pi.height + 4
        if accent and wipe > 0:
            d = ImageDraw.Draw(blk)
            d.rectangle([0, top, bw * wipe, top + mi.height + 2 * pady], fill=self.accent_color + (255,))
        blk.alpha_composite(mi, (padx, top + pady))
        return blk, top + pady + mi.height / 2  # центр главного слова внутри блока

    def draw(self, layer, f, ctx):
        k = self.start + f
        light = self._is_light(k)
        color = INK if light else (255, 255, 255)
        line_y = None
        for i, grp in enumerate(self.groups):
            a, b, text, accent = grp[:4]
            own_y = grp[4] if len(grp) > 4 else None  # высота, подобранная под кадр
            if not (a - 0 <= k < b + 6):
                continue
            g = k - a
            nxt = self.groups[i + 1][0] if i + 1 < len(self.groups) else None
            cont = nxt is not None and nxt - b <= 3  # следующее слово сразу — уходим вверх
            if k < b:
                p = ease_out(g / 6)
                ang, dy, blur, al = (1 - p) * 1.25, (1 - p) * 60, (1 - p) * 26, clamp01(g / 3 + 0.2)
            else:
                q = (k - b) / (4 if cont else 6)
                if q >= 1:
                    continue
                qe = ease_in_out(q)
                if cont:
                    ang, dy, blur, al = -qe * 1.25, -qe * 60, qe * 26, 1 - qe
                else:
                    ang, dy, blur, al = 0, -qe * 20, qe * 18, 1 - qe
            # позиция выбирается на старте группы и не прыгает, пока слово на экране
            self.y = self.light_y if self._is_light(a) else (own_y or self.base_y)
            if k < b:
                line_y = self.y  # линия — под тем словом, что сейчас на экране
            wipe = ease_out((g - 2) / 6) if accent else 0
            plate_txt = (255, 255, 255) if sum(self.accent_color) < 384 else INK
            blk, main_cy = self._block(text, accent, plate_txt if accent else color, wipe)
            img = flip(blk, ang, blur) if (abs(ang) > 0.01 or blur > 1) else blk
            # центр главного слова держим на self.y
            off = main_cy - blk.height / 2
            paste_center(layer, img, W / 2, self.y - off + dy, al)
        # линия под фразой
        for (pa, pb) in self.phrases:
            if not (pa <= k < pb + 6):
                continue
            grow = ease_out((k - pa) / 8)
            shrink = 1 - ease_in_out((k - pb) / 6) if k >= pb else 1
            lw = 520 * grow * shrink
            self.y = line_y if line_y is not None else (
                self.light_y if self._is_light(pa) else self.base_y)
            if lw > 2:
                d = ImageDraw.Draw(layer)
                yy = self.y + self.size * 0.62
                col = (INK if light else (255, 255, 255)) + (int(230 * shrink),)
                d.rectangle([W / 2 - lw / 2, yy, W / 2 + lw / 2, yy + 3], fill=col)


# ---------------------------------------------------------------- карточки

def light_band(img, angle_deg=-32, strength=0.10, seed=0):
    """Мягкая диагональная полоса света/тени на светлом фоне, как в референсе."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle_deg)
    d = xx * math.cos(a) + yy * math.sin(a)
    band = np.exp(-((d - W * 0.15) / 260) ** 2) - 0.6 * np.exp(-((d + W * 0.35) / 180) ** 2)
    arr = np.asarray(img, np.float32)
    arr[..., :3] *= (1 + strength * band[..., None])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), img.mode)


class ColorCard(Element):
    """Полноэкранная цветная карточка (как «ignored» в референсе), въезжает шторкой снизу."""

    def __init__(self, start, dur, color=BORDO, enter=5, exit_=5):
        self.start, self.dur, self.color = start, dur, color
        self.enter, self.exit = enter, exit_
        self.shadow = False
        self.sfx = ("whoosh", 0)

    def draw(self, layer, f, ctx):
        p = ease_out(f / self.enter)
        q = ease_in_out((f - (self.dur - self.exit)) / self.exit)
        top = H * (1 - p) - H * q  # въезд снизу, выезд вверх
        d = ImageDraw.Draw(layer)
        d.rectangle([0, top, W, top + H], fill=self.color + (255,))


class CollageCard(Element):
    """Светлая карточка-коллаж: цветной круг, ч/б вырезка поверх (выходит за круг сверху)."""

    def __init__(self, start, dur, cut, circle=BORDO, circle_r=310, cy=760, cut_h=860,
                 cut_dx=0, enter=7, exit_=5):
        self.start, self.dur, self.cut = start, dur, cut
        self.circle, self.r, self.cy, self.cut_h, self.cut_dx = circle, circle_r, cy, cut_h, cut_dx
        self.enter, self.exit = enter, exit_
        self.shadow = False
        self.sfx = ("whoosh", 0)
        bg = Image.new("RGBA", (W, H), WHITE + (255,))
        self.bg = light_band(bg)
        s = cut_h / cut.height
        self.cut_img = cut.resize((int(cut.width * s), cut_h), Image.LANCZOS)

    def draw(self, layer, f, ctx):
        p = ease_out(f / self.enter)
        q = ease_in_out((f - (self.dur - self.exit)) / self.exit)
        card = self.bg.copy()
        d = ImageDraw.Draw(card)
        # круг с лёгким «перелётом» масштаба
        c = ease_out((f - 1) / 9)
        r = self.r * (c + 0.08 * math.sin(math.pi * c) if c < 1 else 1)
        if r > 1:
            d.ellipse([W / 2 - r, self.cy - r, W / 2 + r, self.cy + r], fill=self.circle + (255,))
        t = ease_out((f - 3) / 9)
        if t > 0:
            ci = self.cut_img
            x = int(W / 2 - ci.width / 2 + self.cut_dx)
            y = int(self.cy + self.r - ci.height + 40 * (1 - t))
            a = np.asarray(ci.getchannel("A"), np.float32) * t
            ci2 = ci.copy()
            ci2.putalpha(Image.fromarray(a.astype(np.uint8)))
            card.alpha_composite(ci2, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
        # въезд: шторка слева направо; выезд: уезжает влево
        x0 = int(-W * (1 - p) - W * q)
        layer.alpha_composite(card, (max(0, x0), 0), (max(0, -x0), 0))


class DuoCard(Element):
    """Светлая карточка «два предмета»: две вырезки рядом, над каждой — подпись-капсула.
    items: [(вырезка RGBA, подпись, цвет капсулы)], слева направо."""

    def __init__(self, start, dur, items, cy=720, item_h=560, gap=40, enter=7, exit_=1):
        self.start, self.dur, self.items = start, dur, items
        self.cy, self.item_h, self.gap = cy, item_h, gap
        self.enter, self.exit = enter, exit_
        self.shadow = False
        self.sfx = ("whoosh", 0)
        self.bg = light_band(Image.new("RGBA", (W, H), WHITE + (255,)))
        self.imgs = []
        for (cut, label, col) in items:
            sc = min(item_h / cut.height, (W - 2 * 20) / len(items) * 1.08 / cut.width)
            self.imgs.append(cut.resize((int(cut.width * sc), int(cut.height * sc)), Image.LANCZOS))

    def draw(self, layer, f, ctx):
        p = ease_out(f / self.enter)
        q = ease_in_out((f - (self.dur - self.exit)) / max(1, self.exit))
        card = self.bg.copy()
        n = len(self.imgs)
        slot = (W - 40) / n
        for i, (img, (cut, label, col)) in enumerate(zip(self.imgs, self.items)):
            t = ease_out((f - 3 - 4 * i) / 9)
            if t <= 0:
                continue
            cx = 20 + slot * (i + 0.5)
            x = int(cx - img.width / 2)
            y = int(self.cy - img.height / 2 + 50 * (1 - t))
            a = np.asarray(img.getchannel("A"), np.float32) * t
            im2 = img.copy()
            im2.putalpha(Image.fromarray(a.astype(np.uint8)))
            card.alpha_composite(im2, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
            # подпись-капсула над предметом
            lt = ease_out((f - 8 - 4 * i) / 8)
            if lt > 0:
                ti = text_image(label, "mont800", 48, (255, 255, 255), spacing=4)
                cw, ch = ti.width + 48, ti.height + 26
                cap = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
                ImageDraw.Draw(cap).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=ch // 2,
                                                      fill=col + (255,))
                cap.alpha_composite(ti, (24, 13))
                ty = self.cy - img.height / 2 - 40 - 20 * (1 - lt)
                paste_center(card, cap, cx, ty, lt)
        x0 = int(-W * (1 - p) - W * q)
        layer.alpha_composite(card, (max(0, x0), 0), (max(0, -x0), 0))


def _icon(kind, size, color):
    """Простые иконки линиями (рисуются сами, без чужих картинок)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = max(3, size // 14)
    c = color + (255,)
    if kind == "scratch":    # три косых штриха
        for i, off in enumerate((-0.22, 0.0, 0.22)):
            x0, y0 = size * (0.28 + off), size * (0.72 - 0.06 * i)
            d.line([x0, y0, x0 + size * 0.34, y0 - size * 0.42], fill=c, width=w)
    elif kind == "heat":     # три волны тепла
        for i in range(3):
            x = size * (0.28 + 0.22 * i)
            pts = [(x + size * 0.06 * math.sin(t / 3), size * 0.18 + size * 0.64 * t / 12)
                   for t in range(13)]
            d.line(pts, fill=c, width=w, joint="curve")
    elif kind == "check":    # галочка
        d.line([size * 0.22, size * 0.52, size * 0.42, size * 0.72, size * 0.8, size * 0.3],
               fill=c, width=w + 1, joint="curve")
    elif kind == "fold":     # зигзаг сгиба
        pts = [(size * 0.16, size * 0.7), (size * 0.38, size * 0.3), (size * 0.6, size * 0.7),
               (size * 0.84, size * 0.3)]
        d.line(pts, fill=c, width=w, joint="curve")
    elif kind == "clock":    # часы
        r = size * 0.34
        d.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], outline=c, width=w)
        d.line([size / 2, size / 2, size / 2, size / 2 - r * 0.62], fill=c, width=w)
        d.line([size / 2, size / 2, size / 2 + r * 0.5, size / 2 + r * 0.2], fill=c, width=w)
    elif kind == "dot":
        r = size * 0.16
        d.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=c)
    return im


def _pop(f, n=9):
    """Пружинка: 0.6 → 1.08 → 1.0."""
    t = clamp01(f / n)
    if t >= 1:
        return 1.0
    return 0.6 + 0.4 * ease_out(t) + 0.12 * math.sin(math.pi * t) * (1 - t)


class Chip(Element):
    """Плашка-иконка (по мотивам референса): белая скруглённая плитка с иконкой и подписью,
    выскакивает с пружинкой возле предмета/рук, уходит сжатием."""

    def __init__(self, start, dur, label, icon="dot", xy=(540, 420), dark=False):
        self.start, self.dur, self.label, self.icon, self.xy = start, dur, label, icon, xy
        self.dark = dark
        self.sfx = ("pop", 0)
        self.shadow_kw = {"radius": 16, "opacity": 0.35}

    def _tile(self):
        bg, fg = (INK, (255, 255, 255)) if self.dark else (WHITE, INK)
        ti = text_image(self.label, "mont800", 40, fg, spacing=3)
        ic = _icon(self.icon, 60, fg)
        h = 112
        w = 30 + ic.width + 16 + ti.width + 34
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(tile).rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=bg + (245,))
        tile.alpha_composite(ic, (30, (h - ic.height) // 2))
        tile.alpha_composite(ti, (30 + ic.width + 16, (h - ti.height) // 2))
        return tile

    def draw(self, layer, f, ctx):
        sc = _pop(f) * (1 - 0.4 * ease_in_out((f - (self.dur - 5)) / 5))
        al = clamp01(f / 3) * (1 - ease_in_out((f - (self.dur - 5)) / 5))
        tile = self._tile()
        # плашка целиком в кадре: отступ 40 px слева, справа не заходит под иконки (x > 960)
        cx = min(max(self.xy[0], 40 + tile.width / 2), 960 - tile.width / 2)
        tile = tile.resize((max(1, int(tile.width * sc)), max(1, int(tile.height * sc))), Image.LANCZOS)
        paste_center(layer, tile, cx, self.xy[1], al)


class CounterChip(Chip):
    """Плашка-счётчик: «СКЛАДКИ  1» → 2 → 5 … ; steps: [(абсолютный кадр, значение)].
    На каждой смене числа — маленькая пружинка цифры и «поп»."""

    def __init__(self, start, dur, label, steps, icon="fold", xy=(540, 420), dark=False):
        super().__init__(start, dur, label, icon, xy, dark)
        self.steps = sorted(steps)

    def pop_frames(self):
        return [k for k, _ in self.steps[1:]]

    def _tile(self):
        k = self._k
        val, since = self.steps[0][1], self.steps[0][0]
        for fk, v in self.steps:
            if k >= fk:
                val, since = v, fk
        bg, fg = (INK, (255, 255, 255)) if self.dark else (WHITE, INK)
        ti = text_image(self.label, "mont800", 40, fg, spacing=3)
        ic = _icon(self.icon, 60, fg)
        num = text_image(str(val), "mont900", 52, fg)
        nsc = _pop(k - since, 6) if since > self.steps[0][0] else 1.0
        num = num.resize((max(1, int(num.width * nsc)), max(1, int(num.height * nsc))), Image.LANCZOS)
        h = 112
        w = 30 + ic.width + 16 + ti.width + 22 + 70 + 30
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(tile).rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=bg + (245,))
        tile.alpha_composite(ic, (30, (h - ic.height) // 2))
        tile.alpha_composite(ti, (30 + ic.width + 16, (h - ti.height) // 2))
        nx = 30 + ic.width + 16 + ti.width + 22 + 35
        tile.alpha_composite(num, (int(nx - num.width / 2), int((h - num.height) / 2)))
        return tile

    def draw(self, layer, f, ctx):
        self._k = self.start + f
        super().draw(layer, f, ctx)


class QuestionMark(Element):
    """Знак «?» в белом круге, выскакивает с пружинкой и слегка покачивается.
    src_point — точка в координатах исходника (едет вместе с зумом плана)."""

    def __init__(self, start, dur, src_point, r=110, dark=False):
        self.start, self.dur, self.src_point, self.r, self.dark = start, dur, src_point, r, dark
        self.sfx = ("pop", 0)
        self.shadow_kw = {"radius": 18, "opacity": 0.35}
        bg, fg = (INK, (255, 255, 255)) if dark else (WHITE, INK)
        d = 2 * r
        self.img = Image.new("RGBA", (d + 8, d + 8), (0, 0, 0, 0))
        ImageDraw.Draw(self.img).ellipse([4, 4, d + 3, d + 3], fill=bg + (250,))
        q = text_image("?", "mont900", int(r * 1.45), fg)
        self.img.alpha_composite(q, ((d + 8 - q.width) // 2, (d + 8 - q.height) // 2 + 2))

    def draw(self, layer, f, ctx):
        x, y = ctx["map"](self.src_point) if ctx.get("map") else self.src_point
        sc = _pop(f, 10) * (1 - 0.5 * ease_in_out((f - (self.dur - 6)) / 6))
        al = clamp01(f / 3) * (1 - ease_in_out((f - (self.dur - 6)) / 6))
        ang = 7 * math.sin(f / 30 * 2 * math.pi * 0.9) * min(1, f / 10)
        bob = 8 * math.sin(f / 30 * 2 * math.pi * 0.6)
        im = self.img.resize((max(1, int(self.img.width * sc)), max(1, int(self.img.height * sc))),
                             Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
        paste_center(layer, im, x, y + bob, al)


def hours_word(n):
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return "ЧАС"
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return "ЧАСА"
    return "ЧАСОВ"


class TimeStat(Element):
    """Плитка «иконка часов + крупное число + ЧАСОВ»: число набегает 1 → value."""

    def __init__(self, start, dur, value, xy=(540, 400), count_frames=16, count=True):
        self.start, self.dur, self.value, self.xy = start, dur, value, xy
        self.count_frames = count_frames
        self.count = count  # False — число сразу целиком (раскрытие интриги, без набегания)
        self.sfx = ("pop", 0)
        self.shadow_kw = {"radius": 18, "opacity": 0.35}

    def tick_frames(self):
        if not self.count:
            return []
        return [self.start + 4 + round(self.count_frames * (i - 1) / max(1, self.value - 1))
                for i in range(2, self.value + 1)]

    def draw(self, layer, f, ctx):
        ticks = [self.start + 4] + self.tick_frames()
        k = self.start + f
        n, since = (1, ticks[0]) if self.count else (self.value, self.start)
        for i, tk in enumerate(ticks if self.count else [], 1):
            if k >= tk:
                n, since = i, tk
        num = text_image(str(n), "mont900", 190, INK)
        nsc = (_pop(k - since, 6) if k >= ticks[0] else 1.0) if self.count else 1.0
        num = num.resize((max(1, int(num.width * nsc)), max(1, int(num.height * nsc))), Image.LANCZOS)
        lab = text_image(hours_word(n), "mont900", 84, INK, spacing=2)
        lab_w = text_image("ЧАСОВ", "mont900", 84, INK, spacing=2).width
        h = 250
        w = 40 + 120 + 36 + 150 + 30 + lab_w + 50
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(tile).rounded_rectangle([0, 0, w - 1, h - 1], radius=48, fill=WHITE + (248,))
        it = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        ImageDraw.Draw(it).rounded_rectangle([0, 0, 119, 119], radius=28, fill=INK + (255,))
        it.alpha_composite(_icon("clock", 92, (255, 255, 255)), (14, 14))
        tile.alpha_composite(it, (40, (h - 120) // 2))
        nx = 40 + 120 + 36 + 75
        tile.alpha_composite(num, (int(nx - num.width / 2), int((h - num.height) / 2)))
        tile.alpha_composite(lab, (40 + 120 + 36 + 150 + 30, (h - lab.height) // 2))
        sc = _pop(f, 10) * (1 - 0.4 * ease_in_out((f - (self.dur - 6)) / 6))
        al = clamp01(f / 3) * (1 - ease_in_out((f - (self.dur - 6)) / 6))
        tile = tile.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS)
        paste_center(layer, tile, self.xy[0], self.xy[1], al)


class ProgressPanel(Element):
    """Панель «иконка + подпись + полоса прогресса» (по мотивам референса).
    Полоса заполняется от fill_from до fill_to (абсолютные кадры)."""

    def __init__(self, start, dur, label, icon="heat", xy=(540, 420), fill_from=None, fill_to=None,
                 width=640, values=None):
        self.start, self.dur, self.label, self.icon, self.xy = start, dur, label, icon, xy
        self.fill_from = start + 8 if fill_from is None else fill_from
        self.fill_to = start + dur - 6 if fill_to is None else fill_to
        self.width = width
        self.values = values  # вместо процентов — подписи по ходу заполнения («1 МЕС» … «1 ГОД»)
        self.sfx = ("pop", 0)
        self.shadow_kw = {"radius": 16, "opacity": 0.35}

    def draw(self, layer, f, ctx):
        k = self.start + f
        w, h = self.width, 168
        panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(panel)
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=WHITE + (245,))
        # иконка в чёрной плитке
        it = Image.new("RGBA", (84, 84), (0, 0, 0, 0))
        ImageDraw.Draw(it).rounded_rectangle([0, 0, 83, 83], radius=20, fill=INK + (255,))
        ic_pop = _pop(f - 3)
        ic = _icon(self.icon, 60, (255, 255, 255))
        it.alpha_composite(ic, (12, 12))
        it = it.resize((max(1, int(84 * ic_pop)), max(1, int(84 * ic_pop))), Image.LANCZOS)
        panel.alpha_composite(it, (int(24 + 42 - it.width / 2), int(h / 2 - it.height / 2)))
        ti = text_image(self.label, "mont800", 36, INK, spacing=3)
        panel.alpha_composite(ti, (132, 32))
        # полоса
        p = ease_in_out((k - self.fill_from) / max(1, self.fill_to - self.fill_from))
        x0, x1, y0 = 132, w - (160 if self.values else 120), 104  # место под подпись справа
        d.rounded_rectangle([x0, y0, x1, y0 + 16], radius=8, fill=LIGHT_GRAY + (255,))
        if p > 0:
            d.rounded_rectangle([x0, y0, x0 + max(16, (x1 - x0) * p), y0 + 16], radius=8, fill=INK + (255,))
        if self.values:
            txt = self.values[min(len(self.values) - 1, int(p * len(self.values) - 1e-6))] if p > 0 \
                else self.values[0]
        else:
            txt = f"{int(round(p * 100))}%"
        pc = text_image(txt, "mont800", 34, INK)
        panel.alpha_composite(pc, (w - 30 - pc.width, y0 + 8 - pc.height // 2))
        sc = _pop(f) * (1 - 0.3 * ease_in_out((f - (self.dur - 5)) / 5))
        al = clamp01(f / 3) * (1 - ease_in_out((f - (self.dur - 5)) / 5))
        panel = panel.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS)
        paste_center(layer, panel, self.xy[0], self.xy[1], al)


class WipeBar(Element):
    """Шторка-переход: цветная полоса проходит через кадр, склейка — под ней (в середине)."""

    def __init__(self, cut_frame, color=BORDO, dur=10):
        self.start, self.dur, self.color = cut_frame - dur // 2, dur, color
        self.shadow = False
        self.sfx = ("whoosh", 0)

    def draw(self, layer, f, ctx):
        p = ease_in_out(f / (self.dur - 1))
        bw = W * 1.1
        x0 = -bw + (W + bw) * p
        d = ImageDraw.Draw(layer)
        d.rectangle([x0, 0, x0 + bw, H], fill=self.color + (255,))


# ---------------------------------------------------------------- звуки

def tone_whoosh(seed=5):
    rng = np.random.default_rng(seed)
    n = int(0.32 * m.SR)
    x = rng.standard_normal(n)
    t = np.arange(n) / n
    # нарастающий и уходящий шум с плавающей «полосой»
    out = np.zeros(n)
    acc = 0.0
    alpha = 0.02 + 0.25 * t ** 1.5
    for i in range(n):
        acc += alpha[i] * (x[i] - acc)
        out[i] = acc
    return out * np.sin(np.pi * t) ** 1.5


m.SFX["whoosh"] = lambda: m.norm_peak(tone_whoosh(), -24)


def tone_pop():
    """Мягкий «поп» интерфейса: короткий тон со спадом высоты."""
    t = np.arange(int(0.09 * m.SR)) / m.SR
    f = 900 + 700 * np.exp(-t * 60)
    ph = 2 * np.pi * np.cumsum(f) / m.SR
    return np.sin(ph) * np.exp(-t * 45)


m.SFX["pop"] = lambda: m.norm_peak(tone_pop(), -26)
