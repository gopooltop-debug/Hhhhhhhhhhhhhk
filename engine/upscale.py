"""Улучшение качества кадров (Real-ESRGAN General x4v3, ONNX, вход 128×128 — работаем тайлами).

    python3 engine/upscale.py вход.mp4 выход.mp4 [--crop w:h:x:y] [--size 1080x1920] [--mix 0.85]

Модель качается с Hugging Face (tamnvcc/Real-ESRGAN-General-x4v3_float).
mix — доля улучшенной картинки (остальное — обычное масштабирование), чтобы лицо не выглядело «пластиковым».
"""
import argparse
import subprocess

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from PIL import Image

T, PAD = 128, 12          # тайл и перекрытие
S = 4                     # масштаб модели


def session():
    p = hf_hub_download("tamnvcc/Real-ESRGAN-General-x4v3_float", "onnx/model.onnx")
    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    return ort.InferenceSession(p, so, providers=["CPUExecutionProvider"])


def sr_frame(sess, img):
    """img: HxWx3 uint8 → (H*4)x(W*4)x3 uint8."""
    h, w, _ = img.shape
    step = T - 2 * PAD
    ny, nx = -(-max(1, h - 2 * PAD) // step), -(-max(1, w - 2 * PAD) // step)
    ph, pw = ny * step + 2 * PAD, nx * step + 2 * PAD
    src = np.pad(img, ((0, ph - h), (0, pw - w), (0, 0)), mode="reflect").astype(np.float32) / 255
    tiles, pos = [], []
    for iy in range(ny):
        for ix in range(nx):
            y, x = iy * step, ix * step
            tiles.append(src[y:y + T, x:x + T].transpose(2, 0, 1))
            pos.append((y, x))
    name = sess.get_inputs()[0].name
    out = np.zeros((ph * S, pw * S, 3), np.float32)
    for t, (y, x) in zip(tiles, pos):
        r = sess.run(None, {name: t[None]})[0][0].transpose(1, 2, 0)
        c = PAD * S
        out[(y + PAD) * S:(y + T - PAD) * S, (x + PAD) * S:(x + T - PAD) * S] = r[c:-c, c:-c]
    # края кадра (первые PAD пикселей) — из обычного масштабирования
    base = np.asarray(Image.fromarray(img).resize((w * S, h * S), Image.BICUBIC), np.float32) / 255
    res = base.copy()
    res[PAD * S:min(h, ph - PAD) * S, PAD * S:min(w, pw - PAD) * S] = \
        out[PAD * S:min(h, ph - PAD) * S, PAD * S:min(w, pw - PAD) * S]
    return (np.clip(res, 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--crop", default=None)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--mix", type=float, default=0.85)
    ap.add_argument("--ss", type=float, default=None)
    ap.add_argument("--t", type=float, default=None)
    a = ap.parse_args()
    W, H = map(int, a.size.split("x"))
    vf = ["fps=30"] + ([f"crop={a.crop}"] if a.crop else [])
    probe = ["ffmpeg", "-v", "error"] + (["-ss", str(a.ss)] if a.ss is not None else []) + \
            (["-t", str(a.t)] if a.t is not None else [])
    r = subprocess.run(probe + ["-i", a.src, "-frames:v", "1", "-vf", ",".join(vf),
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    cw, ch = map(int, a.crop.split(":")[:2]) if a.crop else (None, None)
    w = cw - cw % 2 if cw else None
    h = ch - ch % 2 if ch else None
    vf2 = vf[:-1] + [f"crop={w}:{h}:{a.crop.split(':')[2]}:{a.crop.split(':')[3]}"] if a.crop else vf
    dec = subprocess.Popen(probe + ["-i", a.src, "-vf", ",".join(vf2), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", "30", "-i", "-"] + probe[3:] + ["-i", a.src, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", a.dst],
                           stdin=subprocess.PIPE)
    sess = session()
    n = 0
    while True:
        buf = dec.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        img = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        sr = Image.fromarray(sr_frame(sess, img)).resize((W, H), Image.LANCZOS)
        if a.mix < 1:
            lz = Image.fromarray(img).resize((W, H), Image.LANCZOS)
            sr = Image.blend(lz, sr, a.mix)
        enc.stdin.write(sr.tobytes())
        n += 1
        if n % 15 == 0:
            print("frames", n, flush=True)
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
