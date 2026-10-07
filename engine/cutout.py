"""Вырезание фигур из кадра (BiRefNet lite, ONNX, лицензия MIT) и стилизация под коллаж.

Модель качается с Hugging Face при первом запуске (onnx-community/BiRefNet_lite-ONNX, ~220 МБ).
"""
import numpy as np
from PIL import Image, ImageFilter, ImageOps

_session = None
SIZE = 1024


def _sess():
    global _session
    if _session is None:
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        path = hf_hub_download("onnx-community/BiRefNet_lite-ONNX", "onnx/model.onnx")
        so = ort.SessionOptions()
        so.enable_cpu_mem_arena = False  # иначе память модели не отдаётся до конца процесса
        _session = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
    return _session


def release():
    """Выгрузить модель (перед рендером, чтобы освободить память)."""
    global _session
    _session = None
    import gc
    gc.collect()


def cached(path, make):
    """Вырезка с кэшем на диске: модель запускается только при первом рендере."""
    import os
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    img = make()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path)
    return img


def mask(img):
    """Маска объекта 0..255 (L) для RGB-картинки."""
    s = _sess()
    x = np.asarray(img.convert("RGB").resize((SIZE, SIZE), Image.BILINEAR), np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    out = s.run(None, {s.get_inputs()[0].name: x})[-1][0, 0]
    out = 1 / (1 + np.exp(-out))
    m = Image.fromarray((out * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)
    return m


def cutout(img, box=None):
    """RGBA-вырезка объекта; box — (x0, y0, x1, y1), чтобы взять часть кадра."""
    if box:
        img = img.crop(box)
    m = mask(img)
    rgba = img.convert("RGBA")
    rgba.putalpha(m)
    bb = m.point(lambda v: 255 if v > 40 else 0).getbbox()
    return rgba.crop(bb) if bb else rgba


def collage_style(rgba, contrast=1.35, grain=10, seed=3):
    """Чёрно-белая «журнальная» вырезка: ч/б, контраст, зерно, тонкий светлый край."""
    a = rgba.getchannel("A")
    g = ImageOps.grayscale(rgba.convert("RGB"))
    g = ImageOps.autocontrast(g, cutoff=1)
    arr = np.asarray(g, np.float32)
    arr = (arr - 128) * contrast + 128
    rng = np.random.default_rng(seed)
    arr += rng.normal(0, grain, arr.shape)
    g = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    out = Image.merge("RGBA", (g, g, g, a))
    # мягкая тень под вырезкой
    pad = 40
    canvas = Image.new("RGBA", (out.width + 2 * pad, out.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (20, 20, 20, 0))
    sh.putalpha(Image.new("L", canvas.size, 0))
    sa = Image.new("L", canvas.size, 0)
    sa.paste(a, (pad + 8, pad + 14))
    sa = sa.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.45))
    sh.putalpha(sa)
    canvas.alpha_composite(sh)
    canvas.alpha_composite(out, (pad, pad))
    return canvas
