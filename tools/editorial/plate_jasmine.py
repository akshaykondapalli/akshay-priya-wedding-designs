from common import *

H, W = 2000, 1600
r = np.random.default_rng(7)

# ---- linen ground
nx_ = ndi.gaussian_filter(r.standard_normal((H, W)).astype(np.float32), (0.6, 18))
ny_ = ndi.gaussian_filter(r.standard_normal((H, W)).astype(np.float32), (18, 0.6))
thick = ndi.gaussian_filter(r.standard_normal((H, W)).astype(np.float32), (0.8, 60))
lin = 0.32 * nx_ / nx_.std() + 0.32 * ny_ / ny_.std() + 0.35 * np.clip(thick / thick.std() - 1.3, 0, None)
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
fold = (fbm(H, W, 2, 2, seed=2) - .5)
hfl = ndi.gaussian_filter(lin, .7) * .6 + fold * 60
nl = normals(hfl)
Ld = np.array([-.6, -.7, .55]); Ld /= np.linalg.norm(Ld)
dl = np.clip(((nl * Ld).sum(2) + .4) / 1.4, 0, 1)
linen_lt = hexc('#f3ecdf'); linen_dk = hexc('#cfc0a3')
bg = linen_dk * (1 - dl[..., None]) + linen_lt * dl[..., None]
bg *= (1 + 0.025 * lin[..., None])
fall = np.clip(1.06 - (x / W * .18 + y / H * .22), .7, 1.1)
bg *= fall[..., None]

col = np.zeros((H, W, 3), np.float32)
alpha = np.zeros((H, W), np.float32)


def bez(p0, p1, p2, p3, t):
    t = t[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def put(patch_rgb, patch_a, x0, y0):
    h, w = patch_a.shape
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    pr = patch_rgb[ya - y0:yb - y0, xa - x0:xb - x0]; pa = patch_a[ya - y0:yb - y0, xa - x0:xb - x0]
    col[ya:yb, xa:xb] = col[ya:yb, xa:xb] * (1 - pa[..., None]) + pr * pa[..., None]
    alpha[ya:yb, xa:xb] = alpha[ya:yb, xa:xb] * (1 - pa) + pa


L = np.array([-.55, -.75, .75]); L /= np.linalg.norm(L)
Hv = L + np.array([0, 0, 1.]); Hv /= np.linalg.norm(Hv)
white = hexc('#fbfaf4'); cream = hexc('#d8cfb4'); deep = hexc('#a69a7a'); green = hexc('#6f7a3c'); gdk = hexc('#3d4420')


def ellipsoid(cx, cy, ang, a, b, taper=0.0, flat=1.0, base_col=None, tint=0.0, tip_pink=0.0):
    R = int(max(a, b) + 4)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    c, s = np.cos(ang), np.sin(ang)
    lx = xx * c + yy * s; ly = -xx * s + yy * c
    # taper: narrower towards -a end (stem end)
    bb = b * (1 - taper * np.clip((-lx / a), 0, 1) ** 1.4 * 0.75) * (1 - taper * .55 * np.clip(lx / a, 0, 1) ** 2.2)
    r2 = (lx / a) ** 2 + (ly / bb) ** 2
    inside = smooth(1.0, 0.9, r2)
    nz = np.sqrt(np.clip(1 - r2, 0, 1)) * flat + 0.08
    gx = lx / a ** 2; gy = ly / bb ** 2
    # rotate gradient back to image space
    nxw = gx * c - gy * s; nyw = gx * s + gy * c
    sc = max(a, b)
    n = np.dstack([nxw * sc, nyw * sc, nz]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    d = np.clip((n * L).sum(2), 0, 1)
    sss = np.clip(((n * L).sum(2) + .6) / 1.6, 0, 1)  # wrap = translucency
    spec = np.clip((n * Hv).sum(2), 0, 1) ** 30
    bc = white if base_col is None else base_col
    rgb = deep[None, None] * (1 - sss[..., None]) + bc[None, None] * sss[..., None]
    rgb = rgb * (0.82 + 0.22 * d[..., None]) + spec[..., None] * 0.25
    # green-cream towards the stem end
    st = np.clip(-lx / a, 0, 1)[..., None] ** 2 * tint
    rgb = rgb * (1 - st) + (rgb * hexc('#d6dcae')) * st
    if tip_pink:
        tp = np.clip(lx / a, 0, 1)[..., None] ** 3 * tip_pink
        rgb = rgb * (1 - tp) + rgb * hexc('#f2d6cf') * tp
    put(rgb, inside, int(cx) - R, int(cy) - R)


def calyx(cx, cy, ang, ln):
    # small green sepals + short pedicel toward the thread
    for k in (-0.35, 0.0, 0.35):
        ellipsoid(cx + np.cos(ang + k) * ln * .3, cy + np.sin(ang + k) * ln * .3, ang + k, ln * .45, ln * .12,
                  base_col=green, flat=.6)


# strand path
P = [np.array(p, np.float32) for p in [(1750, 160), (1050, 260), (260, 900), (700, 1500)]]
P2 = [np.array(p, np.float32) for p in [(700, 1500), (1000, 1900), (1300, 2000), (1250, 2250)]]
ts = np.linspace(0, 1, 2000)
pts = np.vstack([bez(*P, ts), bez(*P2, ts)])
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
spacing = 13.0
marks = np.arange(10, seg[-1], spacing)
open_at = set(r.choice(len(marks), 11, replace=False).tolist())

# thread
from PIL import Image as _I, ImageDraw
th = _I.new('L', (W, H), 0); dr = ImageDraw.Draw(th)
dr.line([tuple(p) for p in pts[::6]], fill=255, width=3)
tha = np.asarray(th, np.float32) / 255
col[:] = col * (1 - tha[..., None]) + hexc('#8e8a6e') * tha[..., None]; alpha[:] = np.maximum(alpha, tha)

buds = []
for i, m in enumerate(marks):
    j = np.searchsorted(seg, m)
    p = pts[min(j, len(pts) - 1)]
    tng = pts[min(j + 3, len(pts) - 1)] - pts[max(j - 3, 0)]
    tng = tng / (np.linalg.norm(tng) + 1e-6)
    perp = np.array([-tng[1], tng[0]])
    for k in range(3):
        phi = r.uniform(0, 2 * np.pi)
        ln = r.uniform(42, 54)
        v2 = perp * np.cos(phi) * ln + tng * ln * r.uniform(.25, .5)
        depth = np.sin(phi)
        plen = np.linalg.norm(v2)
        ang = np.arctan2(v2[1], v2[0])
        buds.append((depth, p.copy(), ang, plen, ln))
    if i in open_at:
        buds.append((1.5, p.copy(), None, 0, 0))
buds.sort(key=lambda b: b[0])
for depth, p, ang, plen, ln in buds:
    if ang is None:
        a_out = r.uniform(0, 2 * np.pi)
        cx = p[0] + np.cos(a_out) * 14; cy = p[1] + np.sin(a_out) * 14
        rot = r.uniform(0, np.pi)
        npet = 7
        for k in range(npet):
            aa = rot + k * 2 * np.pi / npet
            ellipsoid(cx + np.cos(aa) * 25, cy + np.sin(aa) * 25, aa, 28, 15, taper=.45, flat=.4)
        ellipsoid(cx, cy, 0, 8, 8, base_col=hexc('#e9e0b0'), flat=.8)
        continue
    a = max(plen * .5, ln * .3)
    cx = p[0] + np.cos(ang) * a * .9; cy = p[1] + np.sin(ang) * a * .9
    shade = .78 + .22 * (depth * .5 + .5)
    bc = white * shade
    ellipsoid(cx, cy, ang, a, ln * .29, taper=.7, tint=.8 * (1 - max(depth, 0)), base_col=bc, tip_pink=r.uniform(0, .35))

# shadow of the strand on linen
sh = ndi.shift(alpha, (34, 26), order=1)
sh = ndi.gaussian_filter(sh, 13) * .55 + ndi.gaussian_filter(ndi.shift(alpha, (8, 6), order=1), 3) * .3
img = bg * (1 - np.clip(sh, 0, .8)[..., None] * np.array([.62, .6, .55]))
img = img * (1 - alpha[..., None]) + col * alpha[..., None]
img = vignette(img, .2)
img = grain(img, .012)
save(img, 'plate-jasmine')
