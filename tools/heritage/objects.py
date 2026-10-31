import sys, math
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFilter
from common import *

OUT = '/home/claude/site/heritage/img/'


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def profile_from_points(pts):
    """pts: list of (y, r) -> callable radius(y) with smooth interpolation."""
    ys = np.array([p[0] for p in pts], np.float32)
    rs = np.array([p[1] for p in pts], np.float32)
    from scipy.interpolate import PchipInterpolator
    f = PchipInterpolator(ys, rs, extrapolate=False)
    def prof(y):
        if y < ys[0] or y > ys[-1]:
            return 0.0
        return float(f(y))
    return prof


def render_lathe(pts, w, h, cx, base='#b8893a', light_dir=(-0.55, -0.45, 0.7)):
    prof = profile_from_points(pts)
    n, a, u = lathe(prof, w, h, cx, 0)
    col = brass(n, u, base, light_dir)
    # subtle hammered texture + tarnish
    tn = noise(h, w, 6, 2)
    col *= (0.92 + 0.12 * tn[..., None])
    tar = np.clip((noise(h, w, 40, 3) - 0.6) * 2.5, 0, 1)
    col = col * (1 - tar[..., None] * 0.35) + hexc('#3b3015') * tar[..., None] * 0.2
    return col, a


def lamp():
    """Standing brass kundulu deepam (samai). 420x980."""
    w, h = 460, 1000
    cx = w / 2
    pts = [
        (8, 0), (10, 150), (16, 172), (26, 180), (34, 176), (40, 160),  # top dish lip + oil bowl
        (60, 120), (80, 72), (92, 40), (100, 30), (112, 34), (122, 28),  # bowl underside into knop
        (140, 22), (160, 30), (172, 26), (190, 18), (300, 16), (316, 26), (330, 18), (360, 15),  # stem rings
        (480, 14), (500, 24), (512, 34), (524, 24), (540, 16), (640, 15), (660, 22), (676, 30),
        (690, 22), (720, 20), (760, 30), (800, 52), (840, 90), (880, 140), (915, 182), (940, 205),
        (955, 212), (968, 214), (980, 210), (990, 0)
    ]
    col, a = render_lathe(pts, w, h, cx)
    # oil surface in the bowl: dark ellipse near top
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    oil = (((x - cx) / 140) ** 2 + ((y - 16) / 9) ** 2) < 1
    col[oil] = col[oil] * 0.25 + hexc('#2a1606') * 0.7
    # five wick points (pancha mukha) at rim positions (front visible: 3)
    save(col, OUT + 'lamp.webp', q=82, alpha=a, size=(230, 500))


def diya(name='diya.webp'):
    """Small brass floor diya (single wick), 3/4 view: 300x160."""
    w, h = 320, 170
    cx = w / 2
    pts = [(30, 0), (32, 120), (40, 130), (52, 124), (70, 100), (90, 70), (104, 44), (112, 40), (124, 52), (136, 60), (150, 56), (160, 0)]
    col, a = render_lathe(pts, w, h, cx)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    oil = (((x - cx) / 110) ** 2 + ((y - 34) / 14) ** 2) < 1
    col[oil] = col[oil] * 0.2 + hexc('#3a1e07') * 0.8
    # lip ring over the oil
    a2 = a.copy()
    save(col, OUT + name, q=82, alpha=a2, size=(160, 85))


def kalasam():
    """Brass kalasam with coconut and mango leaves. 420x620."""
    w, h = 440, 640
    cx = w / 2
    pts = [(250, 0), (252, 70), (262, 78), (276, 70), (300, 92), (340, 150), (390, 190), (450, 200), (510, 180),
           (560, 130), (590, 86), (606, 96), (620, 100), (630, 0)]
    col, a = render_lathe(pts, w, h, cx, base='#c0913e')
    im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # mango leaves fanning out of the mouth (behind coconut)
    leaves = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for i, ang in enumerate(np.linspace(-78, 78, 9)):
        L = mango_leaf(190 + (i % 2) * 26, 54, seed=i)
        L = L.rotate(-ang, resample=Image.BICUBIC, expand=True)
        r = math.radians(ang)
        px = cx + math.sin(r) * 115 - L.width / 2
        py = 245 - math.cos(r) * 100 - L.height / 2
        leaves.alpha_composite(L, (int(px), int(py)))
    canvas.alpha_composite(leaves)
    # coconut: fibrous brown sphere-ish with tuft
    cw, ch = 210, 230
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    u = (xx - cw / 2) / (cw / 2 - 4)
    v = (yy - ch * 0.58) / (ch * 0.42)
    v = np.where(v < 0, v * 0.82, v)
    rr = u ** 2 + v ** 2
    # taper to a point at top
    top = (yy < ch * 0.58)
    taper = 1 - np.clip((ch * 0.58 - yy) / (ch * 0.58), 0, 1) ** 1.6
    u2 = (xx - cw / 2) / np.maximum((cw / 2 - 4) * np.where(top, taper, 1), 1)
    rr = np.where(top, u2 ** 2 + (v * 0.6) ** 2, rr)
    inside = rr < 1
    nz = np.sqrt(np.clip(1 - rr, 0, 1))
    nrm = np.stack([np.where(top, u2, u), v * 0.6, nz], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-6
    fib = ndi.gaussian_filter(RNG.random((ch, cw)).astype(np.float32), (6, 0.7))
    fib = (fib - fib.min()) / (fib.max() - fib.min())
    dif = light(nrm, (-0.5, -0.5, 0.7))
    c = ramp(fib, [(0, '#3d2412'), (0.5, '#7a4f2a'), (1, '#b07d48')]) * (0.3 + 0.8 * dif[..., None])
    ca = np.clip((1 - rr) * 20, 0, 1) * inside
    coco = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    coco.putalpha(Image.fromarray((ca * 255).astype(np.uint8)))
    canvas.alpha_composite(coco, (int(cx - cw / 2), 70))
    canvas.alpha_composite(im)
    # turmeric + kumkum dots on the pot belly
    d = ImageDraw.Draw(canvas)
    d.ellipse([cx - 9, 430 - 9, cx + 9, 430 + 9], fill=(150, 20, 24, 230))
    canvas = canvas.resize((220, 320), Image.LANCZOS)
    canvas.save('/home/claude/tools/heritage/src-img/kalasam.webp', 'WEBP', quality=82, method=6)


def mango_leaf(L=150, W=44, hue='#2f5a22', seed=None):
    rng = np.random.default_rng(seed)
    h, w = L + 10, W + 10
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (yy - 5) / L
    half = (W / 2) * np.clip(np.sin(np.clip(t, 0, 1) * math.pi), 0, 1) ** 0.8 * (1 - 0.25 * t)
    dx = xx - w / 2
    inside = (np.abs(dx) < half) & (t >= 0) & (t <= 1)
    s = dx / np.maximum(half, 1e-3)
    nrm = np.stack([s * 0.6, np.zeros_like(s) - 0.1, np.ones_like(s)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    dif = light(nrm, (-0.4, -0.6, 0.7))
    base = hexc(hue) * (0.5 + 0.7 * dif[..., None])
    mid = np.clip(1 - np.abs(dx) / 1.4, 0, 1)
    base = base * (1 - mid[..., None] * 0.4) + hexc('#a7b86a') * mid[..., None] * 0.4
    veins = (np.abs(np.sin((yy * 0.35 + np.abs(dx) * 0.55))) < 0.12) * 0.12
    base *= (1 - veins[..., None])
    a = np.clip(half - np.abs(dx), 0, 1.5) / 1.5 * inside
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return im


def bud_template(L=46, W=17):
    ss = 3
    h, w = L * ss, W * ss
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = yy / h  # 0 tip .. 1 base
    prof = np.sin(np.clip(t, 0, 1) ** 0.55 * math.pi * 0.92)  # pointed tip, round body, narrow base
    half = (w / 2 - 1) * prof
    dx = (xx - w / 2) / np.maximum(half, 1e-3)
    inside = np.abs(dx) < 1
    nz = np.sqrt(np.clip(1 - dx ** 2, 0, 1))
    nrm = np.stack([dx, (0.5 - t) * 0.6, nz], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    dif = light(nrm, (-0.4, -0.5, 0.75))
    sp = spec(nrm, (-0.4, -0.5, 0.75), 12)
    col = hexc('#f6f1e2') * (0.45 + 0.6 * dif[..., None]) + sp[..., None] * 0.15
    # pink-ish tip on some buds and green base
    green = smoothstep(0.74, 1.0, t)
    col = col * (1 - green[..., None] * 0.8) + hexc('#6f8a3a') * green[..., None] * 0.8 * (0.5 + 0.6 * dif[..., None])
    # subtle petal seams
    seam = (np.abs(np.sin(dx * 3.2)) < 0.12) * (t < 0.6) * 0.08
    col *= (1 - seam[..., None])
    a = (np.clip((1 - np.abs(dx)) * half / 1.5, 0, 1) * inside)
    im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return im.resize((W, L), Image.LANCZOS)


def flower_template(R=26):
    """Open jasmine flower, 5-6 petals."""
    ss = 3
    S = R * 2 * ss
    canvas = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    n = 6
    for i in range(n):
        ang = i / n * 360 + 10
        p = bud_template(int(R * 1.05), int(R * 0.62)).resize((int(R * 0.62 * ss), int(R * 1.05 * ss)), Image.LANCZOS)
        p = p.rotate(180, expand=True)  # base at top (center)
        pc = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        pc.alpha_composite(p, (int(S / 2 - p.width / 2), int(S / 2)))
        pc = pc.rotate(ang, resample=Image.BICUBIC)
        canvas.alpha_composite(pc)
    d = ImageDraw.Draw(canvas)
    c = S / 2
    d.ellipse([c - 5 * ss, c - 5 * ss, c + 5 * ss, c + 5 * ss], fill=(210, 196, 120, 255))
    return canvas.resize((R * 2, R * 2), Image.LANCZOS)


def strand(path_pts, w, h, density=1.0, bud=(40, 15), shadow=True, flowers=0, seed=3, hang=False):
    """Jasmine string along a polyline. Buds tied in pairs pointing outward from the string."""
    rng = np.random.default_rng(seed)
    pts = np.array(path_pts, np.float32)
    # resample by arc length
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    step = bud[1] * 0.95 / density
    ss_ = np.arange(0, s[-1], step)
    xs = np.interp(ss_, s, pts[:, 0]); ys = np.interp(ss_, s, pts[:, 1])
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    tmpl = bud_template(*bud)
    items = []
    for i in range(1, len(xs) - 1):
        tx, ty = xs[i + 1] - xs[i - 1], ys[i + 1] - ys[i - 1]
        ang = math.degrees(math.atan2(ty, tx))
        for side in (-1, 1):
            jitter = rng.normal(0, 20)
            a = ang + 90 * side + jitter
            depth = rng.random()
            items.append((depth, xs[i], ys[i], a, rng.uniform(0.75, 1.15), rng.uniform(0.55, 1.0)))
    items.sort()
    for depth, x, y, a, sc, fs in items:
        t = tmpl.resize((max(4, int(tmpl.width * sc)), max(6, int(tmpl.height * sc * fs))), Image.LANCZOS)
        # template points tip-up; rotate so tip points along angle a
        r = t.rotate(-(a + 90), resample=Image.BICUBIC, expand=True)
        # offset so the base sits on the string
        off = t.height * 0.42
        ox = x + math.cos(math.radians(a)) * off - r.width / 2
        oy = y + math.sin(math.radians(a)) * off - r.height / 2
        if depth < 0.4:
            r = Image.eval(r, lambda v: v) ; rr = np.asarray(r).astype(np.float32); rr[..., :3] *= 0.78; r = Image.fromarray(rr.astype(np.uint8))
        canvas.alpha_composite(r, (int(ox), int(oy)))
    if flowers:
        ft = flower_template(int(bud[0] * 0.62))
        for k in range(flowers):
            i = int(rng.uniform(0.1, 0.9) * len(xs))
            f = ft.rotate(rng.uniform(0, 360), resample=Image.BICUBIC)
            canvas.alpha_composite(f, (int(xs[i] - f.width / 2), int(ys[i] - f.height / 2)))
    if shadow:
        A = np.asarray(canvas)[..., 3].astype(np.float32) / 255
        sh = ndi.gaussian_filter(np.roll(np.roll(A, 10, 0), 8, 1), 7) * 0.75
        base = np.zeros((h, w, 4), np.float32)
        base[..., 3] = sh
        sim = Image.fromarray((base * 255).astype(np.uint8))
        sim.alpha_composite(canvas)
        canvas = sim
    return canvas


def table_jasmine():
    w, h = 900, 520
    rng = np.random.default_rng(5)
    t = np.linspace(0, 1, 60)
    # a loose loop of string lying on the table
    xs = 60 + t * 760 + np.sin(t * 7) * 40
    ys = 380 - np.sin(t * math.pi) * 260 + np.cos(t * 11) * 22
    c1 = strand(list(zip(xs, ys)), w, h, bud=(40, 15), flowers=4, seed=8)
    xs2 = 120 + t * 640
    ys2 = 450 - np.sin(t * math.pi) * 130
    c2 = strand(list(zip(xs2, ys2)), w, h, bud=(36, 14), flowers=2, seed=9)
    c2.alpha_composite(c1)
    c2.save(OUT + 'jasmine-table.webp', 'WEBP', quality=80, method=6)


def hanging_strands(name='jasmine-hang.webp', w=260, h=1400, n=4, seed=11):
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    rng = np.random.default_rng(seed)
    for k in range(n):
        x0 = (k + 0.5) * w / n + rng.normal(0, 6)
        L = h * rng.uniform(0.7, 0.98)
        ys = np.linspace(0, L, 40)
        xs = x0 + np.sin(ys / 160 + k) * 5
        s = strand(list(zip(xs, ys)), w, h, bud=(30, 11), shadow=False, seed=seed + k, flowers=0)
        canvas.alpha_composite(s)
        # marigold/rose bead at the end
        d = ImageDraw.Draw(canvas)
        ex, ey = xs[-1], ys[-1] + 14
        for rr, col in [(14, (196, 96, 14, 255)), (10, (232, 140, 24, 255)), (5, (250, 190, 70, 255))]:
            d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=col)
    canvas.save('/home/claude/tools/heritage/src-img/' + name, 'WEBP', quality=80, method=6)


if __name__ == '__main__':
    which = sys.argv[1:] or ['lamp', 'diya', 'kalasam', 'jasmine', 'hang']
    if 'lamp' in which: lamp()
    if 'diya' in which: diya()
    if 'kalasam' in which: kalasam()
    if 'jasmine' in which: table_jasmine()
    if 'hang' in which: hanging_strands()
