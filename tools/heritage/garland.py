"""Malle (jasmine) garland renderer v2: dense threaded buds, open blossoms, translucency, soft shadow."""
import math, sys
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from common import hexc, light, spec

OUT = '/home/claude/site/heritage/img/'


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def bud(L=44, W=15, tint=0.0, seed=0):
    """Closed jasmine bud, tip at top. Cream-white, translucent rim, green-pink base."""
    rng = np.random.default_rng(seed)
    ss = 4
    h, w = L * ss, W * ss
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = yy / h                          # 0 tip … 1 base
    # long slender bud: pointed tip, fullest at ~35%, long tapering neck (calyx tube)
    prof = np.where(t < 0.36, np.sin(np.clip(t / 0.36, 0, 1) * math.pi / 2) ** 0.75,
                    1 - 0.78 * smooth(0.36, 1.0, t))
    half = (w / 2 - 1) * prof
    dx = (xx - w / 2) / np.maximum(half, 1e-3)
    inside = (np.abs(dx) < 1) & (half > 0.5)
    nz = np.sqrt(np.clip(1 - dx ** 2, 0, 1))
    n = np.stack([dx, (0.35 - t) * 0.5, nz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L_ = (-0.45, -0.55, 0.7)
    dif = light(n, L_)
    sp = spec(n, L_, 14)
    cream = hexc('#fbf7ea')
    col = cream * (0.62 + 0.42 * dif[..., None])
    # translucency: rim glows slightly warmer/brighter instead of going dark
    rim = (1 - nz) ** 2
    col = col * (1 - rim[..., None] * 0.35) + hexc('#fff3d6') * rim[..., None] * 0.35
    # faint pink blush on the lower body of some buds, green calyx at the base
    blush = smooth(0.30, 0.62, t) * (1 - smooth(0.62, 0.8, t)) * (0.25 + 0.5 * tint)
    col = col * (1 - blush[..., None] * 0.35) + hexc('#e8b9b4') * blush[..., None] * 0.35
    green = smooth(0.60, 0.9, t)
    col = col * (1 - green[..., None] * 0.85) + hexc('#7f9845') * green[..., None] * 0.85 * (0.6 + 0.5 * dif[..., None])
    # petal twist lines near the tip (spiral overlap of closed petals)
    twist = np.abs(np.sin((dx * 2.2 + t * 7.0) * math.pi)) < 0.07
    col *= (1 - (twist & (t < 0.38))[..., None] * 0.07)
    col += sp[..., None] * 0.12
    a = np.clip((1 - np.abs(dx)) * half / 2.0, 0, 1) * inside
    a *= (0.93 + 0.07 * nz)  # a touch of translucency
    im = Image.fromarray((np.clip(np.dstack([col, a]), 0, 1) * 255).astype(np.uint8), 'RGBA')
    return im.resize((W, L), Image.LANCZOS)


def blossom(R=22, seed=0):
    """Open five-petal jasmine flower, slightly cupped, with a short green-white throat."""
    rng = np.random.default_rng(seed)
    ss = 4
    S = int(R * 2.2) * ss
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    c = S / 2
    X, Y = (xx - c) / (R * ss), (yy - c) / (R * ss)
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X) + rng.uniform(0, 6.28)
    k = 5
    # petal outline: elongated oval petals, slightly pointed
    ph = (th * k / (2 * math.pi)) % 1 - 0.5           # -0.5..0.5 across a petal
    width = 0.42 * np.sqrt(np.clip(1 - (r / 1.0) ** 2, 0, 1)) + 0.10
    petal = (np.abs(ph) < width * (1.15 - r * 0.6)) & (r < 1.0)
    edge = np.clip((width * (1.15 - r * 0.6) - np.abs(ph)) * 30, 0, 1) * np.clip((1.0 - r) * 30, 0, 1)
    # cupped shading: each petal has a centre crease and lifts at the tip
    nx = np.cos(th) * r * 0.6 + np.sin(ph * math.pi) * 0.35 * -np.sin(th)
    ny = np.sin(th) * r * 0.6 + np.sin(ph * math.pi) * 0.35 * np.cos(th)
    n = np.stack([nx, ny, np.ones_like(r)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    dif = light(n, (-0.45, -0.55, 0.7))
    col = hexc('#fdfaf0') * (0.66 + 0.38 * dif[..., None])
    crease = np.clip(1 - np.abs(ph) * 18, 0, 1) * (r > 0.2)
    col *= (1 - crease[..., None] * 0.06)
    throat = np.clip(1 - r / 0.18, 0, 1)
    col = col * (1 - throat[..., None]) + hexc('#d9d79a') * throat[..., None]
    a = np.maximum(edge * petal, np.clip(1 - r / 0.16, 0, 1))
    im = Image.fromarray((np.clip(np.dstack([col, a]), 0, 1) * 255).astype(np.uint8), 'RGBA')
    return im.resize((S // ss, S // ss), Image.LANCZOS)


def resample(pts, step):
    pts = np.asarray(pts, np.float32)
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    ss_ = np.arange(0, s[-1], step)
    return np.interp(ss_, s, pts[:, 0]), np.interp(ss_, s, pts[:, 1])


def garland(pts, w, h, bud_len=40, density=1.0, blossom_every=11, seed=1, shadow=(9, 11, 8, .55), thread=True):
    rng = np.random.default_rng(seed)
    bw = max(8, int(bud_len * 0.27))
    templates = [bud(bud_len, bw, tint=rng.random(), seed=i) for i in range(10)]
    flowers = [blossom(int(bud_len * 0.5), seed=i) for i in range(4)]
    xs, ys = resample(pts, bw * 0.26 / density)
    items = []
    for i in range(1, len(xs) - 1):
        tx, ty = xs[i + 1] - xs[i - 1], ys[i + 1] - ys[i - 1]
        tang = math.degrees(math.atan2(ty, tx))
        # buds are tied in a spiral: alternate sides, tips swept slightly back along the string
        side = 1 if (i % 2) else -1
        spiral = math.sin(i * 0.9)
        ang = tang + side * (64 + rng.normal(0, 13)) + 16 + rng.normal(0, 5)
        depth = 0.5 + 0.5 * spiral + rng.normal(0, 0.15)    # spiral -> some buds behind, some in front
        fs = 0.74 + 0.26 * abs(math.cos(i * 0.9 + rng.normal(0, .3)))  # foreshortening when pointing at viewer
        sc = rng.uniform(0.86, 1.12)
        items.append(('b', depth, xs[i], ys[i], ang, sc, fs, rng.integers(0, len(templates))))
        if blossom_every and i % blossom_every == 0 and rng.random() < 0.8:
            items.append(('f', 2 + rng.random(), xs[i] + rng.normal(0, 3), ys[i] + rng.normal(0, 3), rng.uniform(0, 360), rng.uniform(0.85, 1.1), 1, rng.integers(0, len(flowers))))
    items.sort(key=lambda it: it[1])
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if thread:
        from PIL import ImageDraw
        d = ImageDraw.Draw(canvas)
        d.line(list(zip(xs, ys)), fill=(86, 92, 48, 255), width=2)
    for kind, depth, x, y, ang, sc, fs, ti in items:
        if kind == 'b':
            t = templates[ti]
            t = t.resize((max(5, int(t.width * sc)), max(7, int(t.height * sc * fs))), Image.LANCZOS)
            # back buds slightly darker (in the garland's own shade)
            if depth < 0.45:
                arr = np.asarray(t).astype(np.float32); arr[..., :3] *= 0.68 + 0.32 * max(depth, 0) / 0.45; t = Image.fromarray(arr.astype(np.uint8))
            r = t.rotate(-(ang + 90), resample=Image.BICUBIC, expand=True)
            off = t.height * 0.46      # base of bud sits on the thread
            ox = x + math.cos(math.radians(ang)) * off - r.width / 2
            oy = y + math.sin(math.radians(ang)) * off - r.height / 2
        else:
            f = flowers[ti]
            f = f.resize((int(f.width * sc), int(f.height * sc)), Image.LANCZOS)
            r = f.rotate(ang, resample=Image.BICUBIC)
            ox, oy = x - r.width / 2, y - r.height / 2
        canvas.alpha_composite(r, (int(round(ox)), int(round(oy))))
    if shadow:
        dx, dy, blur_, op = shadow
        A = np.asarray(canvas)[..., 3].astype(np.float32) / 255
        sh = ndi.gaussian_filter(np.roll(np.roll(A, dy, 0), dx, 1), blur_) * op
        base = np.zeros((h, w, 4), np.uint8)
        base[..., 0:3] = (18, 8, 4)
        base[..., 3] = (np.clip(sh, 0, 1) * 255).astype(np.uint8)
        out = Image.fromarray(base, 'RGBA')
        out.alpha_composite(canvas)
        canvas = out
    return canvas


def catenary(x0, x1, ytop, sag, n=120):
    xs = np.linspace(x0, x1, n)
    m = (x0 + x1) / 2
    a = (x1 - x0) / 2
    # normalised cosh curve: 0 at the ends, sag in the middle
    c = 1.6
    yrel = (np.cosh(c * (xs - m) / a) - np.cosh(c)) / (1 - np.cosh(c))
    return list(zip(xs, ytop + sag * yrel))


def make():
    # arrival: a loose garland lying on the table in a gentle S, plus two loose buds
    t = np.linspace(0, 1, 140)
    xs = 50 + t * 800
    ys = 210 + np.sin(t * math.pi * 1.3 + 0.4) * 90 * (1 - 0.35 * t)
    g = garland(list(zip(xs, ys)), 900, 420, bud_len=40, seed=5, blossom_every=10)
    g.save(OUT + 'jasmine-table.webp', 'WEBP', quality=82, method=6)
    # blessing: a garland draped between two points (catenary), ends trailing
    pts = catenary(40, 860, 40, 120)
    g2 = garland(pts, 900, 230, bud_len=36, seed=9, blossom_every=9, shadow=(6, 10, 7, .5))
    g2.save(OUT + 'jasmine-line.webp', 'WEBP', quality=82, method=6)
    # close-up check sheet
    sheet = Image.new('RGBA', (900, 650), (34, 18, 10, 255))
    sheet.alpha_composite(g, (0, 0)); sheet.alpha_composite(g2, (0, 420))
    sheet.save('/home/claude/qa/heritage/garland-check.png')
    small = Image.new('RGBA', (900, 420), (34, 18, 10, 255)); small.alpha_composite(g)
    small.resize((300, 140), Image.LANCZOS).save('/home/claude/qa/heritage/garland-small.png')


if __name__ == '__main__':
    make()
