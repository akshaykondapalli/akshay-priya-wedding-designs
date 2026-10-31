"""Pelli mandapam night scene, rendered in depth layers (1200x1600 design space)."""
import math, json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFilter
from common import *
from objects import profile_from_points, mango_leaf, strand, bud_template, render_lathe

OUT = '/home/claude/site/heritage/img/'
W, H = 1200, 1600
HORIZON = 900
EXPORT = (900, 1200)
LAMPS = []  # flame positions in design space for the HTML (x, y, scale)


def to_im(rgb, a):
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    im.putalpha(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)))
    return im


def arr(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32) / 255
    return a[..., :3], a[..., 3]


def export(im, name, q=78):
    im.resize(EXPORT, Image.LANCZOS).save(OUT + name, 'WEBP', quality=q, method=6)


# ---------------------------------------------------------------- sky + palms
def sky():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    t = y / HORIZON
    col = ramp(np.clip(t, 0, 1), [(0, '#05070d'), (0.45, '#0b1424'), (0.8, '#2a2030'), (0.95, '#6b3a22'), (1, '#9a5a2a')])
    glow = np.exp(-(((x - W / 2) / 520) ** 2 + ((y - HORIZON) / 260) ** 2))
    col += hexc('#a8582a') * glow[..., None] * 0.45
    below = y > HORIZON
    col[below] = hexc('#1a0f0a')
    # a few faint stars, very sparse (not glitter)
    rng = np.random.default_rng(3)
    st = (rng.random((H, W)) < 0.00025) & (y < HORIZON * 0.6)
    col[st] += 0.35
    col = blur(col, 0.6)
    im = to_im(col, np.ones((H, W)))
    d = ImageDraw.Draw(im)
    # distant palm silhouettes
    rng = np.random.default_rng(8)
    for px in list(rng.uniform(-40, W + 40, 16)):
        h = rng.uniform(150, 300)
        palm(d, px, HORIZON + 10, h, rng, (12, 10, 14, 255))
    # distant village lights (soft warm points) along horizon
    im = im.filter(ImageFilter.GaussianBlur(1.6))
    c, a = arr(im)
    for px in rng.uniform(30, W - 30, 14):
        py = HORIZON + rng.uniform(-6, 14)
        g = np.exp(-(((x - px) ** 2 + (y - py) ** 2) / (2 * rng.uniform(3, 7) ** 2)))
        c += hexc('#f2b46a') * g[..., None] * 0.9
    c = grain(c, 0.012)
    export(to_im(c, np.ones((H, W))), 'm-sky.webp', q=70)


def palm(d, x, base, h, rng, fill):
    lean = rng.uniform(-0.15, 0.15)
    pts = []
    for i in range(20):
        t = i / 19
        pts.append((x + lean * h * t + math.sin(t * 2) * 6, base - h * t))
    for i in range(len(pts) - 1):
        wdt = 7 - 4 * i / 19
        d.line([pts[i], pts[i + 1]], fill=fill, width=int(max(2, wdt)))
    top = pts[-1]
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.42 + rng.normal(0, 0.08)
        L = rng.uniform(55, 85) * h / 240
        prev = top
        for j in range(1, 8):
            tt = j / 7
            px = top[0] + math.cos(a) * L * tt
            py = top[1] + math.sin(a) * L * tt + (L * 0.55) * tt * tt
            d.line([prev, (px, py)], fill=fill, width=max(1, int(4 - tt * 3)))
            # leaflets
            for side in (-1, 1):
                d.line([(px, py), (px + side * 6 * (1 - tt) + math.cos(a + side) * 10, py + 12 * (1 - tt * 0.5))], fill=fill, width=1)
            prev = (px, py)


# ---------------------------------------------------------------- floor + muggu
def muggu_topdown(S=1400):
    """Muggu (rice-flour) design drawn top-down: dot grid, lotus, loops, kumkum/turmeric fills."""
    ss = 2
    im = Image.new('RGBA', (S * ss, S * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S * ss / 2
    white = (246, 240, 226, 255)
    lw = int(5 * ss)
    # outer square with stepped corners
    for r in (560, 530):
        R = r * ss
        d.rectangle([c - R, c - R, c + R, c + R], outline=white, width=lw)
    # dotted border
    for i in range(-24, 25):
        for (xx, yy) in [(c + i * 22 * ss, c - 500 * ss), (c + i * 22 * ss, c + 500 * ss), (c - 500 * ss, c + i * 22 * ss), (c + 500 * ss, c + i * 22 * ss)]:
            if abs(i) <= 22:
                d.ellipse([xx - 4 * ss, yy - 4 * ss, xx + 4 * ss, yy + 4 * ss], fill=white)
    # corner loops (sikku-style arcs around dots)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = c + sx * 400 * ss, c + sy * 400 * ss
            for k in range(3):
                r = (30 + k * 26) * ss
                d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=white, width=lw)
            d.ellipse([cx - 10 * ss, cy - 10 * ss, cx + 10 * ss, cy + 10 * ss], fill=(160, 24, 28, 255))
    # 16-petal lotus, two rings
    for ring, (R0, R1, n, fill) in enumerate([(150, 330, 16, (214, 152, 28, 255)), (90, 210, 8, (160, 24, 28, 255))]):
        for i in range(n):
            a = i / n * 2 * math.pi
            pts = []
            for t in np.linspace(-1, 1, 30):
                ang = a + t * (math.pi / n) * 0.95
                rad = R0 + (R1 - R0) * (1 - t * t) ** 0.6
                pts.append((c + math.cos(ang) * rad * ss, c + math.sin(ang) * rad * ss))
            pts.append((c + math.cos(a + math.pi / n * 0.95) * R0 * ss, c + math.sin(a + math.pi / n * 0.95) * R0 * ss))
            d.polygon(pts, fill=fill if ring == 1 else None, outline=white)
            d.line(pts + [pts[0]], fill=white, width=lw)
    for r, w_ in [(90, lw), (70, lw), (40, 0)]:
        R = r * ss
        if w_:
            d.ellipse([c - R, c - R, c + R, c + R], outline=white, width=w_)
        else:
            d.ellipse([c - R, c - R, c + R, c + R], fill=(214, 152, 28, 255))
    # chain of dots between rings
    for i in range(48):
        a = i / 48 * 2 * math.pi
        xx, yy = c + math.cos(a) * 380 * ss, c + math.sin(a) * 380 * ss
        d.ellipse([xx - 6 * ss, yy - 6 * ss, xx + 6 * ss, yy + 6 * ss], fill=white)
    for i in range(24):
        a = i / 24 * 2 * math.pi
        xx, yy = c + math.cos(a) * 440 * ss, c + math.sin(a) * 440 * ss
        r = 22 * ss
        d.arc([xx - r, yy - r, xx + r, yy + r], 0, 360, fill=white, width=lw)
    im = im.resize((S, S), Image.LANCZOS)
    # powdery edge: erode alpha with noise
    a = np.asarray(im).astype(np.float32) / 255
    nz = noise(S, S, 3, 2)
    a[..., 3] *= np.clip(0.55 + nz * 0.7, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


def floor():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    # stone/earth floor in perspective: tiles converge to vanishing point
    vx, vy = W / 2, HORIZON - 40
    depth = np.clip((y - HORIZON) / (H - HORIZON), 0.001, 1)
    zz = 1 / depth
    u = (x - vx) * depth ** -1 / 300
    v = zz * 1.2
    tex = noise(H, W, 30, 4)
    col = ramp(tex, [(0, '#2a1810'), (0.5, '#3c2416'), (1, '#4e2f1c')])
    # tile seams
    seam = (np.abs(((u + 1000) % 1) - 0.5) > 0.49) | (np.abs((v % 1) - 0.5) > 0.47)
    col[seam] *= 0.82
    # light pool from the mandapam
    pool = np.exp(-(((x - W / 2) / 520) ** 2 + ((y - 1080) / 300) ** 2))
    col *= (0.25 + 1.2 * pool[..., None])
    col *= np.array([1.1, 0.95, 0.8])
    # polished-stone reflections of the lamp row and drape glow
    refl = np.zeros((H, W), np.float32)
    for px in list(range(280, 1000, 80)) + [W / 2]:
        refl += np.exp(-((x - px) ** 2) / (2 * 9 ** 2)) * np.exp(-((y - 1100) / 120) ** 2)
    col += hexc('#ffb060') * refl[..., None] * 0.35
    col *= 0.8
    a = (y > HORIZON - 2).astype(np.float32)
    base = to_im(col, a)
    # muggu warped into perspective on the floor in front of the mandapam
    mg = muggu_topdown(1400)
    # target quad on screen (near wide, far narrow)
    quad = [(330, 1160), (870, 1160), (1180, 1560), (20, 1560)]  # TL, TR, BR, BL on screen
    coeffs = find_coeffs(quad, [(0, 0), (1400, 0), (1400, 1400), (0, 1400)])
    warped = mg.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    wc, wa = arr(warped)
    wc *= (0.25 + 0.75 * pool[..., None])
    wc *= np.array([1.0, 0.92, 0.78])
    warped = to_im(wc, wa * 0.92)
    base.alpha_composite(warped)
    return base


def find_coeffs(pa, pb):
    """coeffs mapping output(pa) -> input(pb) for PIL PERSPECTIVE."""
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    A = np.array(matrix, np.float64)
    B = np.array(pb, np.float64).reshape(8)
    return np.linalg.solve(A, B).tolist()


def lamp_light(c, lamps, ambient=0.16, sigma=240, gain=0.9):
    yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
    L = np.full((H, W), ambient, np.float32)
    for (lx, ly, sc) in lamps:
        L += gain * sc * np.exp(-((xv - lx) ** 2 + (yv - ly) ** 2) / (2 * (sigma * (0.6 + sc * 0.6)) ** 2))
    L = np.clip(L, 0, 1.6)
    tint = np.stack([L * 1.08, L * 0.9, L * 0.68], -1)
    return c * tint


# ---------------------------------------------------------------- mandapam
def wood_lathe(pts, w, h, cx, brass_bands=()):
    prof = profile_from_points(pts)
    n, a, u = lathe(prof, w, h, cx, 0)
    L = (-0.35, -0.3, 0.85)
    dif = light(n, L)
    sp = spec(n, L, 25)
    grainv = ndi.gaussian_filter(RNG.random((h, w)).astype(np.float32), (14, 0.8))
    grainv = (grainv - grainv.min()) / (grainv.max() - grainv.min())
    wood = ramp(grainv, [(0, '#2a1209'), (0.5, '#4a2010'), (1, '#6a301a')])
    col = wood * (0.2 + 1.0 * dif[..., None]) + sp[..., None] * 0.12 * hexc('#ffd9a0')
    from common import brass as brass_shade
    br = brass_shade(n, u, '#c2923f', L)
    ys = np.arange(h)[:, None]
    m = np.zeros((h, w), np.float32)
    for (y0, y1) in brass_bands:
        m = np.maximum(m, ((ys >= y0) & (ys <= y1)).astype(np.float32))
    col = col * (1 - m[..., None]) + br * m[..., None]
    return col, a


def pillar(h=900, scale=1.0):
    """Andhra-style carved pillar: square base block, turned shaft with brass rings, bracket capital."""
    w = int(200 * scale)
    H_ = int(h)
    cx = w / 2
    s = H_ / 900
    pts = [(0, 34), (40, 34), (52, 46), (66, 30), (90, 26), (100, 36), (112, 26), (300, 24), (316, 34), (330, 24),
           (520, 24), (540, 38), (560, 50), (580, 38), (600, 26), (700, 27), (712, 36), (724, 27), (740, 0)]
    pts = [(y * s, r * scale * 1.6) for y, r in pts]
    bands = [(int(40 * s), int(66 * s)), (int(300 * s), int(330 * s)), (int(530 * s), int(590 * s)), (int(700 * s), int(724 * s))]
    col, a = wood_lathe(pts, w, H_, cx, bands)
    im = to_im(col, a)
    d = ImageDraw.Draw(im)
    # square base block (front face + side)
    by = int(740 * s)
    bw = int(150 * scale)
    block = Image.new('RGBA', (w, H_ - by), (0, 0, 0, 0))
    bh = H_ - by
    yy, xx = np.mgrid[0:bh, 0:w].astype(np.float32)
    face = (np.abs(xx - cx) < bw / 2)
    tex = noise(bh, w, 8, 3)
    c = ramp(tex, [(0, '#3a1a0c'), (1, '#5e2c16')])
    # carved horizontal mouldings
    mould = (np.sin(yy / max(bh, 1) * math.pi * 5) > 0.93)
    c[mould] *= 1.25
    c *= 0.7
    shade = np.clip(1 - (xx - (cx - bw / 2)) / bw * 0.6, 0.35, 1)
    c *= shade[..., None]
    block = to_im(c, face.astype(np.float32))
    im.alpha_composite(block, (0, by))
    # bracket capital (potika): stepped beam ends
    top = Image.new('RGBA', (w, int(60 * s)), (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    td.polygon([(cx - 26 * scale * 1.6, top.height), (cx + 26 * scale * 1.6, top.height), (w - 4, 4), (4, 4)], fill=(78, 36, 18, 255))
    td.line([(4, 6), (w - 4, 6)], fill=(200, 150, 70, 255), width=max(1, int(3 * scale)))
    im.alpha_composite(top, (0, 0))
    return im


def banana_leaf(L=520, Wd=150, seed=0, tears=7, dark=0.0):
    rng = np.random.default_rng(seed)
    h, w = L + 20, Wd + 20
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (yy - 10) / L
    half = (Wd / 2) * np.clip(np.sin(np.clip(t, 0, 1) * math.pi * 0.92 + 0.12), 0, 1) ** 0.5
    dx = xx - w / 2
    inside = (np.abs(dx) < half) & (t >= 0) & (t <= 1)
    s = dx / np.maximum(half, 1e-3)
    # lateral veins, slanted
    vein = np.sin((yy - np.abs(dx) * 0.55) * 1.6)
    ridge = 0.04 * vein
    nrm = np.stack([s * 0.5 + ridge * 2, np.zeros_like(s) + ridge, np.ones_like(s)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    dif = light(nrm, (-0.5, -0.3, 0.8))
    base_t = noise(h, w, 40, 3, 0.5, rng)
    col = ramp(base_t, [(0, '#16300f'), (0.5, '#25481a'), (1, '#355e22')]) * (0.45 + 0.8 * dif[..., None])
    mid = np.clip(1 - np.abs(dx) / 4, 0, 1)
    col = col * (1 - mid[..., None] * 0.6) + hexc('#9db35a') * mid[..., None] * 0.6 * (0.5 + 0.5 * dif[..., None])
    col *= (1 - dark)
    a = np.clip(half - np.abs(dx), 0, 1.5) / 1.5 * inside
    # tears: lateral splits from the edge inward
    for _ in range(tears):
        ty = rng.uniform(0.15, 0.95) * L + 10
        side = rng.choice([-1, 1])
        depth = rng.uniform(0.35, 0.9)
        line = np.abs((yy - ty) - (np.abs(dx)) * 0.55) < 1.2
        cut = line & (np.sign(dx) == side) & (np.abs(s) > 1 - depth)
        a[cut] = 0
    # brown dry edge
    edge = np.clip(1 - (half - np.abs(dx)) / 6, 0, 1) * inside
    col = col * (1 - edge[..., None] * 0.5) + hexc('#6b5a2a') * edge[..., None] * 0.5
    # light falloff toward the base
    col *= (0.55 + 0.6 * np.clip(t, 0, 1))[..., None]
    # arch the leaf: rows shift sideways quadratically along its length (pad first, no wrap)
    pad = int(Wd * 0.6)
    oc = np.zeros((h, w + pad, 3), np.float32); oa = np.zeros((h, w + pad), np.float32)
    for r in range(h):
        tr = min(max((r - 10) / L, 0), 1)
        sh = int(tr * tr * pad)
        oc[r, sh:sh + w] = col[r]; oa[r, sh:sh + w] = a[r]
    return to_im(oc, oa)


def banana_plant(h=1000, seed=0, flip=False):
    """Banana plant tied at a doorway: pseudostem + arching leaves."""
    rng = np.random.default_rng(seed)
    w = 700
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # stem
    sw = 70
    cx = w / 2
    pts = [(0, 0), (int(h * 0.42), 0), (int(h * 0.44), sw * 0.42), (int(h * 0.7), sw * 0.48), (h - 2, sw * 0.55), (h, 0)]
    prof = profile_from_points(pts)
    n, a, u = lathe(prof, w, h, cx, 0)
    dif = light(n, (-0.5, -0.2, 0.8))
    fib = ndi.gaussian_filter(rng.random((h, w)).astype(np.float32), (25, 1))
    fib = (fib - fib.min()) / (fib.max() - fib.min())
    stem = ramp(fib, [(0, '#3c4a1c'), (0.5, '#5f6e2a'), (1, '#8e8a46')]) * (0.3 + 0.85 * dif[..., None])
    im.alpha_composite(to_im(stem, a))
    # leaves
    for k in range(7):
        ang = (-60 + k * 20) + rng.normal(0, 6)
        L = rng.uniform(420, 560)
        leaf = banana_leaf(int(L), int(L * 0.27), seed=seed * 10 + k, dark=0.15 * (k % 2))
        # bend: arch the leaf by rotating and shearing
        leaf = leaf.rotate(180, expand=True)  # base at top
        r = leaf.rotate(-ang, resample=Image.BICUBIC, expand=True)
        rad = math.radians(ang)
        ox = cx + math.sin(rad) * L * 0.5 - r.width / 2
        oy = h * 0.42 - math.cos(rad) * L * 0.5 - r.height / 2 + 30
        im.alpha_composite(r, (int(ox), int(oy)))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


def thoranam(width, seed=0):
    """Mango-leaf thoranam: string with pointed leaves hanging, marigold beads between."""
    rng = np.random.default_rng(seed)
    h = 190
    im = Image.new('RGBA', (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n = int(width / 24)
    for i in range(n):
        x = 12 + i * width / n
        sag = 14 * math.sin(math.pi * i / max(n - 1, 1)) + rng.normal(0, 2)
        leaf = mango_leaf(int(rng.uniform(88, 118)), int(rng.uniform(24, 31)), hue=['#24481a', '#2f5a20', '#1c3a14', '#3a5f22'][i % 4], seed=i + seed)
        leaf = leaf.rotate(rng.normal(0, 9), resample=Image.BICUBIC, expand=True)
        lc, la = arr(leaf); lc *= rng.uniform(0.6, 1.0); leaf = to_im(lc, la)
        im.alpha_composite(leaf, (int(x - leaf.width / 2), int(10 + sag)))
    for i in range(n):
        x = 17 + (i + 0.5) * width / n
        sag = 18 * math.sin(math.pi * (i + 0.5) / max(n - 1, 1))
        if i % 2 == 0:
            for rr, col in [(9, (150, 60, 8, 255)), (7, (214, 118, 20, 255)), (3, (246, 176, 54, 255))]:
                d.ellipse([x - rr, 14 + sag - rr, x + rr, 14 + sag + rr], fill=col)
    d.line([(0, 10), (width, 10)], fill=(200, 160, 80, 255), width=3)
    return im


def mandapam():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    # back drape: deep red silk with vertical folds and gold border, behind the platform
    bx0, bx1, by0, by1 = 300, 900, 360, 1000
    m = ((x > bx0) & (x < bx1) & (y > by0) & (y < by1)).astype(np.float32)
    folds = np.sin((x - bx0) / 22 + np.sin(y / 120) * 0.6)
    fn = np.stack([folds * 0.5, np.zeros_like(folds), np.ones_like(folds)], -1)
    fn /= np.linalg.norm(fn, axis=-1, keepdims=True)
    dif = light(fn, (-0.4, -0.2, 0.9))
    silk = hexc('#3e0a0d') * (0.3 + 0.9 * dif[..., None]) + spec(fn, (-0.4, -0.2, 0.9), 30)[..., None] * hexc('#ffb36b') * 0.25
    butta = ((((x - bx0) % 60) - 30) ** 2 + (((y - by0) % 70) - 35) ** 2 < 16) & (m > 0)
    silk[butta] = silk[butta] * 0.3 + hexc('#a8823e') * 0.6
    border = (((x - bx0) < 26) | ((bx1 - x) < 26) | ((y - by0) < 26)) & (m > 0)
    silk[border] = silk[border] * 0.2 + hexc('#b48a3e') * (0.5 + 0.5 * dif[border][..., None])
    glow = np.exp(-(((x - W / 2) / 300) ** 2 + ((y - 760) / 260) ** 2))
    silk *= (0.18 + 0.65 * glow[..., None])
    im.alpha_composite(to_im(silk, m))
    # raised platform (vedika) with steps
    d = ImageDraw.Draw(im)
    plat = [(250, 960), (950, 960), (1010, 1050), (190, 1050)]
    d.polygon(plat, fill=(70, 34, 18, 255))
    d.polygon([(190, 1050), (1010, 1050), (1010, 1085), (190, 1085)], fill=(44, 20, 10, 255))
    d.line([(250, 960), (950, 960)], fill=(200, 150, 70, 255), width=3)
    d.line([(190, 1050), (1010, 1050)], fill=(170, 120, 55, 255), width=3)
    # back pillars (smaller)
    for px in (330, 870):
        p = pillar(640, 0.72)
        im.alpha_composite(p, (int(px - p.width / 2), 330))
    # beam (back)
    d.rectangle([300, 318, 900, 350], fill=(60, 26, 12, 255))
    d.line([(300, 322), (900, 322)], fill=(205, 160, 80, 255), width=3)
    # brass kalasams on the platform, a pair
    k = Image.open('/home/claude/tools/heritage/src-img/kalasam.webp').convert('RGBA')
    k = k.resize((150, 218), Image.LANCZOS)
    for px in (440, 760):
        im.alpha_composite(k, (px - 75, 780))
    # standing lamp at the centre back
    lp = Image.open(OUT + 'lamp.webp').convert('RGBA').resize((120, 260), Image.LANCZOS)
    im.alpha_composite(lp, (W // 2 - 60, 720))
    LAMPS.append((W / 2, 722, 1.0))
    # row of diyas on the platform edge
    dy = Image.open(OUT + 'diya.webp').convert('RGBA').resize((64, 34), Image.LANCZOS)
    for i in range(9):
        px = 280 + i * 80
        im.alpha_composite(dy, (px - 32, 1022))
        LAMPS.append((px, 1022, 0.55))
    # front pillars (big)
    for px in (150, 1050):
        p = pillar(1140, 1.0)
        im.alpha_composite(p, (int(px - p.width / 2), 0 + 70))
    # front beam + canopy
    d.rectangle([0, 50, W, 110], fill=(54, 22, 10, 255))
    d.line([(0, 104), (W, 104)], fill=(205, 160, 80, 255), width=4)
    d.line([(0, 56), (W, 56)], fill=(150, 110, 50, 255), width=2)
    # carved scallops under the beam
    for i in range(0, W, 40):
        d.chord([i, 92, i + 40, 132], 0, 180, fill=(54, 22, 10, 255))
        d.arc([i + 6, 98, i + 34, 126], 0, 180, fill=(190, 140, 64, 255), width=2)
    # jasmine curtain strands hanging from the beam
    hang = Image.open('/home/claude/tools/heritage/src-img/jasmine-hang.webp').convert('RGBA')
    rng2 = np.random.default_rng(4)
    for i, px in enumerate(range(40, W, 150)):
        if 300 < px < 900:
            hh = int(rng2.uniform(260, 360))
        else:
            hh = int(rng2.uniform(640, 860))
        strip = hang.resize((110, hh), Image.LANCZOS)
        sc, sa = arr(strip)
        sc *= np.array([1.0, 0.86, 0.66]) * 0.85  # warm lamplight on white flowers
        im.alpha_composite(to_im(sc, sa), (px - 70, 120))
    th = thoranam(W, 3)
    im.alpha_composite(th, (0, 100))
    # global warm light falloff
    c, a = arr(im)
    c = lamp_light(c, LAMPS + [(W / 2, 700, 1.4), (W / 2, 250, 0.5)], ambient=0.2, sigma=260, gain=0.8)
    vert = np.clip(0.5 + (y / 750), 0.5, 1.0)
    c *= vert[..., None]
    c = grain(c, 0.01)
    return to_im(c, a)


def foreground():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    left = banana_plant(1300, seed=1)
    right = banana_plant(1300, seed=2, flip=True)
    im.alpha_composite(left, (-420, 330))
    im.alpha_composite(right, (W - 280, 330))
    # brass diyas in the foreground floor
    dy = Image.open(OUT + 'diya.webp').convert('RGBA')
    for px, py, s in [(140, 1500, 1.25), (1060, 1500, 1.25), (330, 1420, 0.95), (870, 1420, 0.95)]:
        dd = dy.resize((int(160 * s), int(85 * s)), Image.LANCZOS)
        im.alpha_composite(dd, (int(px - dd.width / 2), int(py)))
        LAMPS.append((px, py, 1.35 * s))
    c, a = arr(im)
    yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
    c = lamp_light(c, LAMPS[-4:] + [(W / 2, 900, 1.0)], ambient=0.2, sigma=300, gain=0.6)
    # depth of field: soften the foreground leaves (not the diyas)
    leafmask = (yv < 1380).astype(np.float32)
    cb = blur(c * a[..., None], 3.0); ab = blur(a, 3.0)
    cb = cb / np.maximum(ab[..., None], 1e-3)
    c = c * (1 - leafmask[..., None]) + cb * leafmask[..., None]
    a = a * (1 - leafmask) + ab * leafmask
    return to_im(c, a)


if __name__ == '__main__':
    sky()
    fl = floor()
    export(fl, 'm-floor.webp', 72)
    md = mandapam()
    export(md, 'm-mandapam.webp', 78)
    fg = foreground()
    export(fg, 'm-front.webp', 76)
    json.dump(LAMPS, open('/home/claude/tools/heritage/lamps.json', 'w'))
    # preview composite
    comp = Image.open(OUT + 'm-sky.webp').convert('RGBA')
    for n_ in ['m-floor.webp', 'm-mandapam.webp', 'm-front.webp']:
        comp.alpha_composite(Image.open(OUT + n_).convert('RGBA'))
    comp.save('/home/claude/qa/heritage/scene.png')
