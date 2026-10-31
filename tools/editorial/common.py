import numpy as np
from scipy import ndimage as ndi
from PIL import Image
import os

OUT = '/home/claude/site/editorial/img'
RAW = '/home/claude/tools/editorial/raw'
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
rng = np.random.default_rng(21112026)


def fbm(h, w, octaves=5, base=8, persist=0.55, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gh, gw = base * 2 ** o, int(base * 2 ** o * w / h) + 1
        g = r.standard_normal((gh + 1, gw + 1)).astype(np.float32)
        z = ndi.zoom(g, (h / gh, w / gw), order=3)[:h, :w]
        out += amp * z; tot += amp; amp *= persist
    out /= tot
    return (out - out.min()) / (np.ptp(out) + 1e-9)


def normals(hf, strength=1.0):
    gy, gx = np.gradient(hf * strength)
    n = np.dstack([-gx, -gy, np.ones_like(hf)])
    return n / np.linalg.norm(n, axis=2, keepdims=True)


def light(n, d):
    d = np.array(d, np.float32); d /= np.linalg.norm(d)
    return np.clip((n * d).sum(2), 0, 1)


def grain(img, amt=0.018, seed=3):
    r = np.random.default_rng(seed)
    g = r.standard_normal(img.shape[:2]).astype(np.float32)
    g = ndi.gaussian_filter(g, 0.6)
    return img + amt * g[..., None]


def vignette(img, strength=0.25, power=2.2):
    h, w = img.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / 1.414
    return img * (1 - strength * d[..., None] ** power)


def save(img, name, sizes=((1200, None), (720, None)), q=80):
    img = np.clip(img, 0, 1)
    im = Image.fromarray((img * 255).astype(np.uint8))
    im.save(f'{RAW}/{name}.png')
    paths = []
    for wd, _ in sizes:
        ht = round(im.height * wd / im.width)
        p = f'{OUT}/{name}-{wd}.webp'
        im.resize((wd, ht), Image.LANCZOS).save(p, 'WEBP', quality=q, method=6)
        paths.append((p, os.path.getsize(p)))
    print(name, [(os.path.basename(a), b // 1024) for a, b in paths])


def hexc(s):
    s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
