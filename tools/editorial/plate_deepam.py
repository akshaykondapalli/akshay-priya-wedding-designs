from common import *

H, W = 2000, 1600
S = 1.75                     # world -> px
CX, BASEY = W / 2, 1640      # screen position of the foot centre
th = np.deg2rad(16)          # camera looks down 16 deg
ct, st = np.cos(th), np.sin(th)


def prof(h):
    """outer radius profile of a brass kundulu (standing deepam)."""
    r = np.zeros_like(h)
    # foot
    m = h < 30; r[m] = 250 - (h[m] / 30) ** 3 * 8
    m = (h >= 30) & (h < 125); t = (h[m] - 30) / 95; r[m] = 242 - 170 * (np.sin(t * np.pi / 2)) ** 0.8
    # stem with lathe beads
    m = (h >= 125) & (h < 540); hh = h[m]
    rr = 34 + 4 * np.sin(hh / 9)
    for c, a, w in [(150, 40, 18), (232, 30, 14), (300, 22, 9), (360, 46, 20), (440, 24, 9), (500, 34, 15)]:
        rr = np.maximum(rr, 34 + a * np.sqrt(np.clip(1 - ((hh - c) / w) ** 2, 0, 1)))
    r[m] = rr
    # under bowl cup
    m = (h >= 540) & (h < 612); t = (h[m] - 540) / 72; r[m] = 40 + 70 * t ** 1.6
    # bowl flare
    m = (h >= 612) & (h <= 700); t = (h[m] - 612) / 88; r[m] = 110 + 105 * np.sin(t * np.pi / 2) ** 1.2 + 12 * np.clip((t - .85) / .15, 0, 1) ** 2
    return r


TOP = 700.0; OIL = 676.0; TH = 9.0
hs = np.linspace(0, TOP, 3400).astype(np.float32)
phis = np.linspace(-np.pi, np.pi, 3600, endpoint=False).astype(np.float32)

zbuf = np.full((H, W), -1e9, np.float32)
nbuf = np.zeros((H, W, 3), np.float32)
hbuf = np.zeros((H, W), np.float32)
kind = np.zeros((H, W), np.int8)   # 1 brass outer, 2 brass inner, 3 rim, 4 oil


def splat(X, Y, Z, N, HH, k):
    xi = np.round(CX + X * S).astype(np.int32); yi = np.round(BASEY + Y * S).astype(np.int32)
    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
    xi, yi, Z, N, HH = xi[ok], yi[ok], Z[ok], N[ok], HH[ok]
    order = np.argsort(Z)            # far first, near last overwrites
    xi, yi, Z, N, HH = xi[order], yi[order], Z[order], N[order], HH[order]
    lin = yi * W + xi
    # keep last occurrence (nearest) per pixel
    _, idx = np.unique(lin[::-1], return_index=True)
    idx = len(lin) - 1 - idx
    sel = Z[idx] > zbuf.ravel()[lin[idx]]
    idx = idx[sel]
    zbuf.ravel()[lin[idx]] = Z[idx]
    nbuf.reshape(-1, 3)[lin[idx]] = N[idx]
    hbuf.ravel()[lin[idx]] = HH[idx]
    kind.ravel()[lin[idx]] = k


def surface(hs_, rfun, inward=False, k=1):
    hh, pp = np.meshgrid(hs_, phis, indexing='ij')
    r = rfun(hh)
    dr = np.gradient(rfun(hs_), hs_)[:, None] * np.ones_like(pp)
    nx, ny, nz = np.cos(pp), -dr, np.sin(pp)        # world normal (y up)
    if inward: nx, ny, nz = -nx, dr, -nz
    wx, wy, wz = r * np.cos(pp), hh, r * np.sin(pp)
    # camera: rotate around x so we look down
    X = wx; Y = -(wy * ct) + wz * st; Z = wz * ct + wy * st
    nvx = nx; nvy = -(ny * ct) + nz * st; nvz = nz * ct + ny * st   # screen-space normal, y down
    N = np.stack([nvx, nvy, nvz], -1).reshape(-1, 3)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    splat(X.ravel(), Y.ravel(), Z.ravel(), N, hh.ravel(), k)


surface(hs, prof, k=1)
hin = np.linspace(616, TOP, 900).astype(np.float32)
surface(hin, lambda h: prof(h) - TH, inward=True, k=2)


def disk(h, r0, r1, k, n=(0, 1, 0)):
    rr, pp = np.meshgrid(np.linspace(r0, r1, 700).astype(np.float32), phis, indexing='ij')
    wx, wz = rr * np.cos(pp), rr * np.sin(pp); wy = np.full_like(rr, h)
    X = wx; Y = -(wy * ct) + wz * st; Z = wz * ct + wy * st
    N = np.tile(np.array([0, -ct, st], np.float32), (X.size, 1))
    splat(X.ravel(), Y.ravel(), Z.ravel(), N, wy.ravel(), k)


rt = prof(np.array([TOP], np.float32))[0]
disk(TOP, rt - TH, rt, 3)
disk(OIL, 0, prof(np.array([OIL], np.float32))[0] - TH, 4)

# fill splat holes
mask = zbuf > -1e8
for _ in range(2):
    hole = ~mask & ndi.binary_dilation(mask, iterations=1) & ndi.binary_erosion(ndi.binary_dilation(mask, iterations=2), iterations=1)
    if not hole.any(): break
    for arr in (nbuf[..., 0], nbuf[..., 1], nbuf[..., 2], hbuf):
        arr[hole] = ndi.maximum_filter(np.where(mask, arr, -9), 3)[hole]
    kind[hole] = ndi.maximum_filter(kind, 3)[hole]
    mask = mask | hole
mask_f = ndi.gaussian_filter(mask.astype(np.float32), .7)

# ---------- shading
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
n = nbuf
V = np.array([0, 0, 1.], np.float32)
ndv = np.clip(n[..., 2], 0, 1)
R = 2 * ndv[..., None] * n - V                       # reflection vector, screen space (y down)
# environment: dark warm room, tall softbox at left, warm flame glow above, floor
rx, ry, rz = R[..., 0], R[..., 1], R[..., 2]
env = 0.05 + 0.10 * np.clip(-ry, 0, 1)               # upward = slightly brighter
soft = np.exp(-((rx + 0.62) / 0.16) ** 2) * np.exp(-((ry + 0.05) / 0.55) ** 2) * (rz > -0.2)
soft2 = np.exp(-((rx - 0.7) / 0.10) ** 2) * np.exp(-((ry + 0.1) / 0.4) ** 2) * 0.35
floor = np.clip(ry, 0, 1) * 0.12
env = env + 2.0 * soft + soft2 * 1.6 + floor
brass = hexc('#d4a64a'); brass_dk = hexc('#5a3a12')
# lathe rings / brushing
ring = 0.88 + 0.12 * np.sin(hbuf * 2.1) * np.sin(hbuf * 0.37 + 1) + 0.05 * np.sin(hbuf * 13)
fres = 0.75 + 0.25 * (1 - ndv) ** 3
key = np.clip(((n * np.array([-.6, -.35, .72])).sum(2)), 0, 1)
metal = (brass_dk[None, None] * (0.7 + 0.9 * key[..., None]) + brass[None, None] * env[..., None] * 1.25) * (ring * fres)[..., None]

# flame point light
FX, FY, FZ = 0.0, -(TOP + 70) * ct + (rt - 40) * st, 0  # roughly above front lip
fx_s, fy_s = CX + 0 * S, BASEY + (-(TOP + 10) * ct + (rt - 18) * st) * S
flame_y = fy_s - 120
lv = np.dstack([fx_s - xx, flame_y - yy, np.full_like(xx, 220)])
dist = np.linalg.norm(lv, axis=2); lv /= dist[..., None]
fl = np.clip((n * lv).sum(2), 0, 1) * (420 / (dist + 260)) ** 2
metal += fl[..., None] * hexc('#ffb45a') * 0.9

# oil surface: dark amber mirror with flame reflection
oil = hexc('#3a2208') * (0.6 + 0.4 * ndi.gaussian_filter((kind == 4).astype(np.float32), 30)[..., None])
glint = np.exp(-(((xx - fx_s) / 26) ** 2 + ((yy - (fy_s + 10)) / 9) ** 2))
oil = oil + glint[..., None] * hexc('#ffcf7a') * 1.2
obj = np.where((kind == 4)[..., None], oil, metal)
# inner bowl slightly darker (occluded)
obj = np.where((kind == 2)[..., None], obj * 0.72 + fl[..., None] * hexc('#ffb45a') * .4, obj)

# ---------- backdrop: low-key umber with flame warmth, stone ledge
bg_top = hexc('#2b2219'); bg_bot = hexc('#16110c')
t = (yy / H)[..., None]
bg = bg_top * (1 - t) + bg_bot * t
halo = np.exp(-(((xx - fx_s) / 520) ** 2 + ((yy - flame_y) / 460) ** 2))
bg = bg + halo[..., None] * hexc('#6a4220') * 0.55
ledge_y = BASEY + 40
ledge = yy > ledge_y - 30 + 0.0 * xx
bg = np.where(ledge[..., None], bg * 0.75 + hexc('#2a2017') * 0.25, bg)
# soft contact shadow under foot
cs = np.exp(-(((xx - CX) / 470) ** 2 + ((yy - (BASEY + 10)) / 34) ** 2))
bg *= (1 - 0.6 * cs[..., None])

img = bg * (1 - mask_f[..., None]) + obj * mask_f[..., None]

# reflection on the polished ledge
refl = np.flipud(img[ledge_y - 900 - 0:ledge_y, :]) if False else None
src = img.copy()
k0 = int(ledge_y)
span = min(H - k0, 420)
mirror = src[k0 - span:k0][::-1]
fade = np.linspace(0.22, 0, span)[:, None, None]
img[k0:k0 + span] = img[k0:k0 + span] * (1 - fade) + ndi.gaussian_filter(mirror, (6, 2, 0)) * fade

# ---------- flame (additive)
fxx = (xx - fx_s) / 30; fyy = (yy - (fy_s - 98)) / 108
core = np.exp(-(fxx ** 2 * (1 + 1.6 * np.clip(-fyy, 0, 3)) + (fyy * (1.25 if True else 1)) ** 2))
inner = np.exp(-(((xx - fx_s) / 12) ** 2 + ((yy - (fy_s - 58)) / 38) ** 2))
blue = np.exp(-(((xx - fx_s) / 12) ** 2 + ((yy - (fy_s - 10)) / 10) ** 2))
glow = np.exp(-(((xx - fx_s) / 200) ** 2 + ((yy - (fy_s - 110)) / 220) ** 2))
img += core[..., None] * hexc('#ffb347') * 1.1 + inner[..., None] * hexc('#fff3d6') * 1.3 \
    + blue[..., None] * hexc('#5a6bd8') * .25 + glow[..., None] * hexc('#ff9a3d') * .28
# wick
wk = np.exp(-(((xx - fx_s) / 3.2) ** 2 + ((yy - (fy_s + 2)) / 9) ** 2))
img = img * (1 - wk[..., None] * .8) + wk[..., None] * hexc('#2a1a0c') * .8

img = vignette(img, .35)
img = grain(img, .016)
# gentle filmic tone curve
img = img / (1 + 0.18 * img)
save(img, 'plate-deepam')
