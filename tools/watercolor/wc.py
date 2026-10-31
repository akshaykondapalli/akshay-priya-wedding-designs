"""A small physically-inspired watercolor renderer.

Model: paintings are made on pure white (transmittance 1). Each wash multiplies the
canvas by a pigment transmittance weighted by a density field, so glazes stack like
real transparent watercolor. The result is displayed with mix-blend-mode: multiply
over the page's paper texture.

Effects per wash: displaced (bleeding) edge, wet-edge darkening, density mottling,
pigment granulation into paper valleys, cauliflower blooms / back-runs.
"""
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw

RNG = np.random.default_rng(7)


def seed(s):
    global RNG
    RNG = np.random.default_rng(s)


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


# ---------- noise ----------
def noise(shape, scale, wrap=False):
    n = RNG.standard_normal(shape).astype(np.float32)
    n = ndi.gaussian_filter(n, scale, mode='wrap' if wrap else 'reflect')
    n -= n.mean()
    n /= (n.std() + 1e-6)
    return n


def fbm(shape, scales=(2, 6, 18, 48), weights=None, wrap=False):
    weights = weights or [1.0 / (i + 1) for i in range(len(scales))]
    out = np.zeros(shape, np.float32)
    for s, w in zip(scales, weights):
        out += w * noise(shape, s, wrap)
    out -= out.min()
    out /= out.max() + 1e-6
    return out


# ---------- paper ----------
def paper_height(shape, wrap=False):
    h = fbm(shape, scales=(1.2, 3.5, 9, 22), weights=[0.35, 0.45, 0.35, 0.25], wrap=wrap)
    return h


def paper_tile(size=768, base='#f8f2e7'):
    h = paper_height((size, size), wrap=True)
    gy, gx = np.gradient(ndi.gaussian_filter(h, 1.0, mode='wrap'))
    shade = 1 + 9.0 * (gx - gy)
    shade = np.clip(shade, 0.80, 1.12)
    col = hexrgb(base)[None, None, :] * (0.965 + 0.035 * shade[..., None])
    # faint large mottling of sizing
    mott = fbm((size, size), scales=(40, 90), wrap=True)
    col *= (0.985 + 0.02 * mott[..., None])
    return np.clip(col, 0, 1)


# ---------- shapes ----------
class Canvas:
    def __init__(self, w, h, ss=2):
        self.w, self.h, self.ss = w, h, ss
        self.c = np.ones((h, w, 3), np.float32)
        self.paper = paper_height((h, w))
        self.wx = noise((h, w), 6) * 1.0 + noise((h, w), 22) * 1.6
        self.wy = noise((h, w), 6) * 1.0 + noise((h, w), 22) * 1.6
        self.mot = fbm((h, w), scales=(8, 26, 70))
        self.lx = noise((h, w), 1.5)
        self.ly = noise((h, w), 1.5)

    # mask helpers: draw only inside the bbox of the geometry -------------------
    def _draw(self, shapes):
        """shapes: list of ('poly', pts) | ('ell', (x0,y0,x1,y1))"""
        xs, ys = [], []
        for kind, g in shapes:
            if kind == 'poly':
                xs += [p[0] for p in g]; ys += [p[1] for p in g]
            else:
                xs += [g[0], g[2]]; ys += [g[1], g[3]]
        x0 = int(max(0, np.floor(min(xs)) - 2)); y0 = int(max(0, np.floor(min(ys)) - 2))
        x1 = int(min(self.w, np.ceil(max(xs)) + 3)); y1 = int(min(self.h, np.ceil(max(ys)) + 3))
        out = np.zeros((self.h, self.w), np.float32)
        if x1 <= x0 or y1 <= y0:
            return out
        s = self.ss
        im = Image.new('L', ((x1 - x0) * s, (y1 - y0) * s), 0)
        d = ImageDraw.Draw(im)
        for kind, g in shapes:
            if kind == 'poly':
                d.polygon([((x - x0) * s, (y - y0) * s) for x, y in g], fill=255)
            else:
                d.ellipse([(g[0] - x0) * s, (g[1] - y0) * s, (g[2] - x0) * s, (g[3] - y0) * s], fill=255)
        im = im.resize((x1 - x0, y1 - y0), Image.BILINEAR)
        out[y0:y1, x0:x1] = np.asarray(im, np.float32) / 255.0
        return out

    def poly(self, pts):
        return self._draw([('poly', pts)])

    def polys(self, lst):
        return self._draw([('poly', p) for p in lst])

    def ellipse(self, cx, cy, rx, ry):
        return self._draw([('ell', (cx - rx, cy - ry, cx + rx, cy + ry))])

    def _dabs(self, pts, widths):
        pts = np.asarray(pts, np.float32)
        widths = np.broadcast_to(np.asarray(widths, np.float32), (len(pts),))
        seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
        L = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(L[-1] / 1.0))
        t = np.linspace(0, L[-1], n)
        xs = np.interp(t, L, pts[:, 0]); ys = np.interp(t, L, pts[:, 1]); ws = np.interp(t, L, widths)
        return [('ell', (x - max(w / 2, .3), y - max(w / 2, .3), x + max(w / 2, .3), y + max(w / 2, .3)))
                for x, y, w in zip(xs, ys, ws)]

    def stroke(self, pts, widths):
        return self._draw(self._dabs(pts, widths))

    def strokes(self, items):
        sh = []
        for pts, w in items:
            sh += self._dabs(pts, w)
        return self._draw(sh)

    # region helpers ---------------------------------------------------------
    def _bbox(self, m, pad):
        rows = np.flatnonzero(m.max(1) > 0.003)
        if len(rows) == 0:
            return None
        cols = np.flatnonzero(m[rows[0]:rows[-1] + 1].max(0) > 0.003)
        y0 = max(0, rows[0] - pad); y1 = min(self.h, rows[-1] + pad + 1)
        x0 = max(0, cols[0] - pad); x1 = min(self.w, cols[-1] + pad + 1)
        return (slice(y0, y1), slice(x0, x1))

    def _warp(self, m, amt, sl, fx=None, fy=None):
        if amt <= 0:
            return m
        fx = self.wx if fx is None else fx
        fy = self.wy if fy is None else fy
        y0, x0 = sl[0].start, sl[1].start
        hh, ww = m.shape
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        return ndi.map_coordinates(m, [yy + fy[sl] * amt, xx + fx[sl] * amt], order=1, mode='nearest')

    def warp(self, m, amt):
        sl = (slice(0, self.h), slice(0, self.w))
        return self._warp(m, amt, sl)

    def wash(self, mask, pigment, opacity=0.5, bleed=3.0, soft=1.2, edge=0.55,
             mottle=0.35, gran=0.45, blooms=0, bloom_size=40, edge_width=None,
             local_warp=None):
        ew = edge_width or max(2.5, bleed * 1.3)
        pad = int(bleed * 5 + soft * 3 + ew * 3 + (local_warp[0] * 2 if local_warp else 0) + 8)
        sl = self._bbox(mask, pad)
        if sl is None:
            return
        m = mask[sl]
        if local_warp:
            m = self._warp(m, local_warp[0], sl, self.lx, self.ly)
        m = self._warp(m, bleed, sl)
        if soft > 0:
            m = ndi.gaussian_filter(m, soft)
        m = np.clip(m, 0, 1)
        inner = ndi.gaussian_filter(m, ew)
        rim = np.clip(m - inner, 0, 1)
        rim = rim / (rim.max() + 1e-6)
        dens = m * opacity
        if mottle:
            dens *= (1 - mottle / 2) + mottle * self.mot[sl]
        dens += rim * edge * opacity * (m > 0.05)
        if blooms:
            for _ in range(blooms):
                ys, xs = np.nonzero(m > 0.6)
                if len(xs) == 0:
                    break
                i = RNG.integers(len(xs))
                rr = bloom_size * RNG.uniform(0.6, 1.4)
                b = self.ellipse(xs[i] + sl[1].start, ys[i] + sl[0].start, rr, rr * RNG.uniform(0.7, 1.2))[sl]
                b = self._warp(b, bleed * 2.5 + 3, sl)
                b = ndi.gaussian_filter(b, 1.5)
                brim = np.clip(b - ndi.gaussian_filter(b, 3), 0, 1)
                brim /= brim.max() + 1e-6
                dens = dens * (1 - 0.45 * b) + brim * 0.35 * opacity * m
        if gran:
            dens *= 1 + gran * (0.5 - self.paper[sl]) * 2.0
        dens = np.clip(dens, 0, 1)[..., None]
        if isinstance(pigment, np.ndarray) and pigment.ndim == 3:
            pig = pigment[sl]
        else:
            pig = hexrgb(pigment) if isinstance(pigment, str) else np.asarray(pigment, np.float32)
        self.c[sl] *= 1 - dens * (1 - pig)

    def lift(self, mask, amount=0.5, soft=2):
        sl = self._bbox(mask, int(soft * 3 + 12))
        if sl is None:
            return
        m = ndi.gaussian_filter(self._warp(mask[sl], 2, sl), soft)[..., None] * amount
        self.c[sl] = self.c[sl] * (1 - m) + m

    def glow(self, cx, cy, r, color, strength=0.6):
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
        g = np.exp(-d ** 2 * 2.2)
        g = self.warp(g, 6)
        self.c = self.c * (1 - g[..., None] * strength) + g[..., None] * strength * hexrgb(color)

    def gradient_field(self, stops, axis='y', warp=12):
        h, w = self.h, self.w
        t = np.linspace(0, 1, h if axis == 'y' else w)
        cols = np.stack([np.interp(t, [s[0] for s in stops], [hexrgb(s[1])[k] for s in stops]) for k in range(3)], -1)
        if axis == 'y':
            f = np.broadcast_to(cols[:, None, :], (h, w, 3)).copy()
        else:
            f = np.broadcast_to(cols[None, :, :], (h, w, 3)).copy()
        if warp:
            for k in range(3):
                f[..., k] = self.warp(f[..., k], warp)
        return f

    def deckle(self, cx=None, cy=None, rx=None, ry=None, power=2.2, rough=40, feather=30, mask=None):
        h, w = self.h, self.w
        if mask is None:
            cx = w / 2 if cx is None else cx
            cy = h / 2 if cy is None else cy
            rx = w * 0.5 if rx is None else rx
            ry = h * 0.5 if ry is None else ry
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            d = (np.abs((xx - cx) / rx) ** power + np.abs((yy - cy) / ry) ** power) ** (1 / power)
            d = d + (self.mot - 0.5) * 0.25
            mask = np.clip((1 - d) * rough, 0, 1)
        mask = ndi.gaussian_filter(self.warp(mask, 8), feather / 10)
        self.c = self.c * mask[..., None] + (1 - mask[..., None])

    def save(self, path, q=76, size=None, alpha=True, aq=55):
        """Save as RGBA: the multiply-on-paper look converted to straight alpha, so the
        painting composites correctly over the page paper without blend modes."""
        M = np.clip(self.c, 0, 1)
        if alpha:
            P = hexrgb('#f8f2e6')[None, None, :]
            mn = M.min(-1, keepdims=True)
            a = np.clip(1 - mn, 0, 1)
            C = np.where(a > 1e-3, P * (M - mn) / np.maximum(a, 1e-3), 0)
            rgba = np.concatenate([np.clip(C, 0, 1), a], -1)
            img = Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA')
        else:
            img = Image.fromarray((M * 255).astype(np.uint8))
        if size:
            img = img.resize(size, Image.LANCZOS)
        img.save(path, quality=q, alpha_quality=aq, method=6)
        return img


# ---------- botanical primitives (return polygons) ----------
def leaf_poly(cx, cy, length, width, ang, n=24, curve=0.15):
    t = np.linspace(0, 1, n)
    half = np.sin(np.pi * t) ** 0.9 * width / 2
    bend = curve * length * np.sin(np.pi * t)
    xs = t * length
    top = np.stack([xs, half + bend], 1)
    bot = np.stack([xs[::-1], (-half + bend)[::-1]], 1)
    p = np.concatenate([top, bot])
    c, s = np.cos(ang), np.sin(ang)
    R = np.array([[c, -s], [s, c]])
    p = p @ R.T + [cx, cy]
    return [tuple(v) for v in p]


def petal_poly(cx, cy, length, width, ang, n=20, tip=1.0):
    t = np.linspace(0, 1, n)
    half = (np.sin(np.pi * t ** 0.8) ** 0.8) * width / 2 * (1 - 0.3 * t ** 3 * tip)
    xs = t * length
    p = np.concatenate([np.stack([xs, half], 1), np.stack([xs[::-1], -half[::-1]], 1)])
    c, s = np.cos(ang), np.sin(ang)
    p = p @ np.array([[c, -s], [s, c]]).T + [cx, cy]
    return [tuple(v) for v in p]


def bezier(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)
