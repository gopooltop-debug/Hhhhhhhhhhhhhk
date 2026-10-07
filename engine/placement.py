"""Подбор высоты текста под кадр: как можно ближе к центру, но не закрывая лицо
и не закрывая предмет целиком.

Препятствия ищет модель вырезки (BiRefNet):
  - план с человеком (talking=True): голова — верхняя часть маски человека (~580 px от макушки),
    её закрывать нельзя; тело почти не штрафуется (руки с предметом можно закрыть частично);
  - предметный план: вся маска (предмет + руки), закрывать минимально.
Маски считаются на 3 кадрах плана с учётом зума и кэшируются на диске.
"""
import json
import os

import numpy as np
from PIL import Image

import cutout as co
import montage as m

CENTER = 960
CANDIDATES = list(range(700, 1361, 20))
BOX_X = (120, 960)
BOX_UP, BOX_DOWN = 130, 85     # над центром слова — приставка, под ним — линия
HEAD_H = 580


def _zoomed(mask, seg, f):
    z = seg.zoom(f, seg.length)
    if len(z) == 3 and not isinstance(z[1], tuple):
        sc, dx, dy = z
        foc, tgt = seg.center, (seg.center[0] + dx, seg.center[1] + dy)
    else:
        sc, foc, tgt = z
    arr = np.repeat(np.asarray(mask)[..., None], 3, axis=2)
    out, _ = m.transform(arr, sc, foc, tgt)
    return out[..., 0].astype(np.float32) / 255


def obstacles(img, talking):
    mk = np.asarray(co.mask(img), np.float32) / 255
    if not talking:
        return mk
    rows = np.where((mk > 0.5).sum(1) > 40)[0]
    ob = mk * 0.08
    if len(rows):
        top = rows[0]
        ob[top:top + HEAD_H] = np.maximum(ob[top:top + HEAD_H], (mk[top:top + HEAD_H] > 0.3) * 1.0)
    return ob


def best_y(ob):
    x0, x1 = BOX_X
    best, by = 1e9, CENTER
    for y in CANDIDATES:
        band = ob[max(0, y - BOX_UP):min(m.H, y + BOX_DOWN), x0:x1]
        score = float(band.mean()) + 0.25 * abs(y - CENTER) / 400
        if score < best:
            best, by = score, y
    return by


def plan_y(segments, default_src, grab, cache_path):
    """{индекс плана: y}. grab(файл, сек) -> PIL RGB-кадр."""
    cache = {}
    if os.path.exists(cache_path):
        cache = json.load(open(cache_path))
    res = {}
    for i, s in enumerate(segments):
        vf = s.video_file or default_src
        key = f"{os.path.basename(vf)}:{s.vin}:{s.length}:{s.video_file is None}"
        if key in cache:
            res[i] = cache[key]
            continue
        talking = s.video_file is None
        acc = np.zeros((m.H, m.W), np.float32)
        for f in (3, s.length // 2, max(0, s.length - 4)):
            img = grab(vf, (s.vin + f) / m.FPS)
            ob = obstacles(img, talking)
            ob_img = Image.fromarray((np.clip(ob, 0, 1) * 255).astype(np.uint8))
            acc = np.maximum(acc, _zoomed(ob_img, s, f))
        res[i] = cache[key] = best_y(acc)
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    json.dump(cache, open(cache_path, "w"))
    return res
