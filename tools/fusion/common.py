import numpy as np
from scipy import ndimage as ndi
from PIL import Image
import subprocess, os, base64

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = '/home/claude/site/fusion/img'
TMP = os.path.join(HERE, 'tmp')
os.makedirs(TMP, exist_ok=True)

rng = np.random.default_rng(21112026)


def noise(h, w, scale, seed=None):
    """Smooth value noise in [0,1] with feature size ~scale px."""
    r = np.random.default_rng(seed) if seed is not None else rng
    sh, sw = max(2, int(h / scale) + 3), max(2, int(w / scale) + 3)
    n = r.random((sh, sw)).astype(np.float32)
    z = ndi.zoom(n, (h / (sh - 3) + 1e-6, w / (sw - 3) + 1e-6), order=3)
    z = z[:h, :w]
    z = (z - z.min()) / (z.max() - z.min() + 1e-6)
    return z


def fbm(h, w, base, octaves=5, persistence=0.5, seed=0):
    tot = np.zeros((h, w), np.float32)
    amp, s, norm = 1.0, base, 0
    for i in range(octaves):
        tot += amp * noise(h, w, max(s, 1.5), seed + i * 17)
        norm += amp
        amp *= persistence
        s /= 2
    return tot / norm


def blur(a, s):
    if a.ndim == 3:
        return np.stack([ndi.gaussian_filter(a[..., i], s) for i in range(a.shape[2])], -1)
    return ndi.gaussian_filter(a, s)


def load(path):
    return np.asarray(Image.open(path).convert('RGBA')).astype(np.float32) / 255


def save(arr, name, q=80, size=None, alpha=False):
    a = np.clip(arr, 0, 1)
    mode = 'RGBA' if alpha else 'RGB'
    if not alpha and a.shape[2] == 4:
        a = a[..., :3]
    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8), mode)
    if size:
        im = im.resize(size, Image.LANCZOS)
    p = os.path.join(OUT, name)
    im.save(p, 'WEBP', quality=q, method=6)
    print(name, im.size, os.path.getsize(p) // 1024, 'KB')
    return p


def render_svg(svg, w, h, name, transparent=False):
    sp = os.path.join(TMP, name + '.svg')
    pp = os.path.join(TMP, name + '.png')
    open(sp, 'w').write(svg)
    subprocess.run(['node', os.path.join(HERE, 'render.js'), sp, pp, str(w), str(h)] + (['t'] if transparent else []), check=True)
    return load(pp)


def font_b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()


def grain(h, w, amt=0.035, seed=5):
    r = np.random.default_rng(seed)
    g = r.normal(0, 1, (h, w)).astype(np.float32)
    g = ndi.gaussian_filter(g, 0.6)
    return g[..., None] * amt


def screen(a, b):
    return 1 - (1 - a) * (1 - b)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)
