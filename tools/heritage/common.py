"""Shared procedural helpers for the Heritage artwork."""
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RNG = np.random.default_rng(2111)
FONTS = '/home/claude/tools/heritage/node_modules/@fontsource'


def font(name, size):
    paths = {
        'csc': f'{FONTS}/cormorant-sc/files/cormorant-sc-latin-600-normal.woff',
        'cg': f'{FONTS}/cormorant-garamond/files/cormorant-garamond-latin-500-normal.woff',
        'cgi': f'{FONTS}/cormorant-garamond/files/cormorant-garamond-latin-500-italic.woff',
    }
    return ImageFont.truetype(paths[name], size)


def noise(h, w, scale, octaves=5, persistence=0.5, rng=RNG):
    """Fractal value noise in [0,1]. scale = feature size in px of first octave."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        up = ndi.zoom(g, (h / (gh - 1) * 1.0001, w / (gw - 1) * 1.0001), order=3)[:h, :w]
        out += amp * up
        tot += amp
        amp *= persistence
        s /= 2
        if s < 1:
            break
    out /= tot
    out -= out.min()
    out /= max(out.max(), 1e-6)
    return out


def blur(a, s):
    if a.ndim == 3:
        return np.stack([ndi.gaussian_filter(a[..., i], s) for i in range(a.shape[2])], -1)
    return ndi.gaussian_filter(a, s)


def lerp(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def ramp(t, stops):
    """t: HxW in [0,1]; stops: list of (pos, '#hex')."""
    t = np.clip(t, 0, 1)
    out = np.zeros(t.shape + (3,), np.float32)
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        m = (t >= p0) & (t <= p1)
        k = ((t - p0) / max(p1 - p0, 1e-6))[m][:, None]
        out[m] = hexc(c0) * (1 - k) + hexc(c1) * k
    return out


def normals(height, strength=1.0):
    gy, gx = np.gradient(height * strength)
    n = np.stack([-gx, -gy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def light(n, d):
    d = np.array(d, np.float32)
    d /= np.linalg.norm(d)
    return np.clip((n * d).sum(-1), 0, 1)


def spec(n, d, power=20):
    d = np.array(d, np.float32); d /= np.linalg.norm(d)
    h = d + np.array([0, 0, 1], np.float32); h /= np.linalg.norm(h)
    return np.clip((n * h).sum(-1), 0, 1) ** power


def grain(img, amt=0.03, rng=RNG):
    g = rng.normal(0, amt, img.shape[:2]).astype(np.float32)[..., None]
    return img + g


def save(arr, path, q=80, alpha=None, size=None):
    arr = np.clip(arr, 0, 1)
    im = Image.fromarray((arr * 255).astype(np.uint8))
    if alpha is not None:
        im.putalpha(Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)))
    if size:
        im = im.resize(size, Image.LANCZOS)
    im.save(path, 'WEBP', quality=q, method=6)
    return im


def mask_from_draw(w, h, fn, ss=2):
    im = Image.new('L', (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    fn(d, ss)
    if ss > 1:
        im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def lathe(profile, w, h, cx, y0, light_dir=(-0.6, -0.4, 0.7), env=None):
    """Render a surface of revolution.
    profile: function y(px from y0) -> radius px (0 = no surface). Returns rgb(HxWx3 normal-ish), alpha, n
    Returns normals, alpha so the caller can shade with any material."""
    ys = np.arange(h, dtype=np.float32)
    r = np.array([profile(y) for y in ys], np.float32)
    dr = np.gradient(r)
    X = np.arange(w, dtype=np.float32)[None, :] - cx
    R = r[:, None]
    inside = (np.abs(X) < R) & (R > 0.5)
    u = np.where(inside, X / np.maximum(R, 1e-3), 0)
    nz = np.sqrt(np.clip(1 - u ** 2, 0, 1))
    slope = -dr[:, None]  # radius increasing downwards -> normal tilts down
    n = np.stack([u, np.broadcast_to(slope, u.shape) * nz, nz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
    # antialias the silhouette
    edge = np.clip(R - np.abs(X), 0, 1.5) / 1.5
    alpha = np.where(R > 0.5, edge, 0).astype(np.float32)
    return n, alpha, u


def brass(n, u, base='#b8893a', light_dir=(-0.5, -0.5, 0.75), warm=(1.0, 0.75, 0.4), rng=RNG):
    """Polished brass shading with a fake environment (dark room, warm lamp)."""
    h, w = n.shape[:2]
    # environment: reflect vector x component -> horizontal bands
    rx = n[..., 0]
    ry = n[..., 1]
    envv = 0.10 + 0.9 * np.exp(-((rx + 0.45) ** 2) / 0.02) + 0.35 * np.exp(-((rx - 0.55) ** 2) / 0.05)
    envv += 0.25 * np.exp(-((ry + 0.6) ** 2) / 0.05)
    diff = light(n, light_dir)
    sp = spec(n, light_dir, 60)
    col = hexc(base)
    dark = hexc('#3a2410')
    c = dark * (1 - diff[..., None]) * 0.9 + col * (0.25 + 0.75 * diff[..., None])
    c = c * (0.55 + 0.6 * envv[..., None])
    c += np.array(warm) * sp[..., None] * 1.2
    return c
