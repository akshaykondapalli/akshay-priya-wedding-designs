from common import *

H, W = 2000, 1600
r = np.random.default_rng(12)
L = np.array([-0.55, -0.3, 0.62]); L /= np.linalg.norm(L)
stone_lt = hexc('#d3b994'); stone_dk = hexc('#34261a'); stone_mid = hexc('#b49a78')


def xsection(nsides, R, alpha, ncols):
    """for each column across [-R*1.5, R*1.5] -> (inside, nx, nz) of the front-most face."""
    xs = np.linspace(-1.5 * R, 1.5 * R, ncols)
    ang = alpha + np.arange(nsides) * 2 * np.pi / nsides
    vx, vz = R * np.cos(ang), R * np.sin(ang)
    best = np.full(ncols, -1e9); nxo = np.zeros(ncols); nzo = np.zeros(ncols)
    for i in range(nsides):
        x0, z0, x1, z1 = vx[i], vz[i], vx[(i + 1) % nsides], vz[(i + 1) % nsides]
        ex, ez = x1 - x0, z1 - z0
        nx, nz = ez, -ex
        nn = np.hypot(nx, nz); nx, nz = nx / nn, nz / nn
        if (nx * (x0 + x1) + nz * (z0 + z1)) < 0: nx, nz = -nx, -nz
        if nz <= 0: continue
        lo, hi = min(x0, x1), max(x0, x1)
        m = (xs >= lo) & (xs <= hi) & (abs(ex) > 1e-6)
        zc = z0 + (xs[m] - x0) / (ex if abs(ex) > 1e-6 else 1) * ez
        upd = zc > best[m]
        idx = np.where(m)[0][upd]
        best[idx] = zc[upd]; nxo[idx] = nx; nzo[idx] = nz
    inside = best > -1e8
    return xs, inside, nxo, nzo


def pillar(w=220, h=1500):
    """returns rgba float array (h, W2) of a carved Andhra-style mandapam pillar"""
    W2 = int(w * 2.2)
    rgb = np.zeros((h, W2, 3), np.float32); a = np.zeros((h, W2), np.float32)
    hb = np.zeros((h, W2), np.float32)  # relief height for medallions
    cx = W2 / 2
    # (y0, y1 fractions from top, kind, scale)
    secs = [
        (0.00, 0.035, 4, 1.95), (0.035, 0.07, 4, 1.55), (0.07, 0.11, 32, 0.95),  # corbel + abacus + neck
        (0.11, 0.17, 32, 1.15), (0.17, 0.19, 32, 0.8),
        (0.19, 0.34, 4, 1.0), (0.34, 0.36, 32, 0.92), (0.36, 0.47, 8, 0.95), (0.47, 0.49, 32, 0.92),
        (0.49, 0.64, 4, 1.0), (0.64, 0.66, 32, 0.92), (0.66, 0.76, 8, 0.95), (0.76, 0.78, 32, 0.92),
        (0.78, 0.92, 4, 1.0), (0.92, 0.95, 4, 1.18), (0.95, 1.0, 4, 1.32),
    ]
    tex = fbm(h, W2, 5, 6, seed=r.integers(1e6)) - .5
    speck = ndi.gaussian_filter(r.standard_normal((h, W2)).astype(np.float32), .7)
    for (f0, f1, kind, sc) in secs:
        y0, y1 = int(f0 * h), int(f1 * h)
        R = w / 2 * sc
        alpha = np.deg2rad(22) if kind != 32 else 0
        xs, inside, nx, nz = xsection(kind, R, alpha, int(3 * R))
        x0 = int(cx - 1.5 * R)
        cols = np.arange(len(xs)) + x0
        ok = (cols >= 0) & (cols < W2) & inside
        c = cols[ok]
        d = np.clip(nx[ok] * L[0] + nz[ok] * L[2], 0, 1)
        shade = 0.22 + 0.9 * d
        seg = (y1 - y0)
        yy = np.arange(seg)[:, None]
        # bevel/overhang shading: top edge lit, bottom edge dark
        edge = np.ones((seg, 1))
        edge[:2] *= 1.25; edge[-3:] *= 0.55
        # occlusion below wider section above: gradient at top
        occ = 1 - 0.35 * np.exp(-yy / 14.0)
        val = shade[None, :] * edge * occ
        rgb[y0:y1, c] = (stone_dk[None, None] * (1 - val[..., None]) + stone_lt[None, None] * val[..., None]).clip(0, 1.2)
        a[y0:y1, c] = 1
        # relief medallion on square blocks: lotus rosette on the lit front face
        if kind == 4 and 0.15 < f0 < 0.9:
            mcx = cx + R * 0.18; mcy = (y0 + y1) / 2; mr = min(R * 0.62, seg * 0.42)
            Y, X = np.mgrid[y0:y1, int(mcx - mr - 2):int(mcx + mr + 2)]
            dx, dy = (X - mcx) / mr, (Y - mcy) / mr
            rr = np.hypot(dx, dy); th = np.arctan2(dy, dx)
            petals = np.clip(np.cos(th * 8) * 0.5 + 0.5, 0, 1) ** 0.6
            rel = ((rr < 1) * (0.6 + 0.4 * petals * (rr > .35)) * (1 - rr ** 4)
                   + (rr < .3) * .5 - (np.abs(rr - .36) < .03) * .5 - (np.abs(rr - .98) < .03) * .6)
            Xc = np.clip(X, 0, W2 - 1)
            hb[Y, Xc] = np.maximum(hb[Y, Xc], rel)
        # flutes on octagons
    # relief lighting
    hbs = ndi.gaussian_filter(hb, 1.2) * 9
    gy, gx = np.gradient(hbs)
    nrel = np.dstack([-gx, -gy, np.ones_like(gx)]); nrel /= np.linalg.norm(nrel, axis=2, keepdims=True)
    lrel = np.clip((nrel * L).sum(2), 0, 1) / L[2]
    rgb *= (0.55 + 0.45 * lrel[..., None]) * (hb > 0)[..., None] + (hb <= 0)[..., None]
    # stone texture + vertical weathering streaks
    streak = ndi.gaussian_filter(r.standard_normal((h, W2)).astype(np.float32), (40, 1.5))
    streak = streak / (streak.std() + 1e-6)
    rgb *= (1 + 0.30 * tex[..., None] + 0.07 * speck[..., None] - 0.07 * np.clip(streak, 0, None)[..., None])
    # face edges: thin highlight where the visible face changes (crisp arrises)
    lum = rgb.mean(2)
    ed = np.abs(np.diff(lum, axis=1, prepend=lum[:, :1])) > 0.06
    ed = ndi.binary_dilation(ed, iterations=1) & (a > .5)
    rgb[ed] = rgb[ed] * 0.75 + stone_lt * 0.25
    # incised grooves every ~18px on round bands/neck (horizontal dark lines)
    yy_ = np.arange(h)[:, None]
    groove = ((yy_ % 16) < 2) & (yy_ > int(.07 * h)) & (yy_ < int(.19 * h))
    rgb[np.broadcast_to(groove, a.shape) & (a > .5)] *= 0.78
    # pushpa potika: two droplet pendants hanging from corbel ends
    for side in (-1, 1):
        px = cx + side * w * 0.82; py = int(0.035 * h)
        Y, X = np.mgrid[py:py + int(0.07 * h), int(px - 30):int(px + 30)]
        t = (Y - py) / (0.07 * h)
        prof = 26 * np.sin(np.pi * np.clip(t, 0, 1) ** .7) * (1 - t * .35)
        m = np.abs(X - px) < prof
        dxn = (X - px) / (prof + 1e-3)
        d = np.clip(-dxn * L[0] + np.sqrt(np.clip(1 - dxn ** 2, 0, 1)) * L[2], 0, 1)
        v = (0.22 + 0.9 * d)[..., None]
        col = stone_dk * (1 - v) + stone_lt * v
        Xc = np.clip(X, 0, W2 - 1)
        rgb[Y[m], Xc[m]] = col[m]; a[Y[m], Xc[m]] = 1
    a = ndi.gaussian_filter(a, .6)
    return rgb, a


def place(canvas, cov, rgb, a, x, y, scale, blur, haze, haze_col):
    from PIL import Image as I
    hh, ww = a.shape
    nw, nh = max(1, int(ww * scale)), max(1, int(hh * scale))
    im = I.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), I.LANCZOS)
    am = I.fromarray((a * 255).astype(np.uint8)).resize((nw, nh), I.LANCZOS)
    rr = np.asarray(im, np.float32) / 255; aa = np.asarray(am, np.float32) / 255
    rr = rr * (1 - haze) + haze_col * haze
    big = np.zeros((H, W, 3), np.float32); ba = np.zeros((H, W), np.float32)
    x0, y0 = int(x - nw / 2), int(y)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + nh)
    if xa >= xb or ya >= yb: return
    big[ya:yb, xa:xb] = rr[ya - y0:yb - y0, xa - x0:xb - x0]
    ba[ya:yb, xa:xb] = aa[ya - y0:yb - y0, xa - x0:xb - x0]
    if blur > 0.3:
        big = ndi.gaussian_filter(big * ba[..., None], (blur, blur, 0))
        ba = ndi.gaussian_filter(ba, blur)
        big = big / np.maximum(ba[..., None], 1e-4)
    canvas[:] = canvas * (1 - ba[..., None]) + big * ba[..., None]
    cov[:] = np.maximum(cov, ba)


# ---------- backdrop: dusk sky through the hall, distant palms
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
sky = hexc('#f6dcb4') * (1 - yy[..., None] / H) + hexc('#e9b98a') * (yy[..., None] / H)
sun = np.exp(-(((xx - 1150) / 420) ** 2 + ((yy - 980) / 360) ** 2))
img = sky + sun[..., None] * hexc('#fff1d6') * 0.5
# distant palm silhouettes (very blurred)
pal = np.zeros((H, W), np.float32)
from PIL import Image as I, ImageDraw
pim = I.new('L', (W, H), 0); dr = ImageDraw.Draw(pim)
for px in [880, 1040, 1330, 1480]:
    top = 760 + r.integers(-60, 60)
    dr.line([(px, 1500), (px + r.integers(-30, 30), top)], fill=255, width=14)
    for k in range(9):
        ang = -np.pi / 2 + (k - 4) * 0.42
        dr.line([(px, top), (px + np.cos(ang) * 170, top + np.sin(ang) * 80 + 60)], fill=255, width=22)
pal = ndi.gaussian_filter(np.asarray(pim, np.float32) / 255, 12)
img = img * (1 - pal[..., None] * .35) + hexc('#b98c66') * pal[..., None] * .35
# horizon haze band + paddy line
hz = np.exp(-((yy - 1420) / 90) ** 2)
img = img * (1 - hz[..., None] * .3) + hexc('#f2d6b0') * hz[..., None] * .3

# ---------- perspective scene
VPX, VPY = 1700.0, 1080.0
TOP0, BOT0 = 150.0, 1650.0     # pillar top/bottom at scale 1 (height 1500)
def P(s, X0):
    return VPX - s * (VPX - X0), VPY - s * (VPY - TOP0), VPY + s * (BOT0 - VPY)

# floor plane: below the line through pillar bases
floor_line = lambda x: VPY + (BOT0 - VPY) * (VPX - x) / (VPX - 360) * 1.0
fy = floor_line(xx)
fl = yy > fy
fcol = hexc('#7a5e44') * (0.7 + 0.5 * np.clip((yy - VPY) / (H - VPY), 0, 1))[..., None]
img = np.where(fl[..., None], fcol, img)
# beam underside / architrave along tops
cov = np.zeros((H, W), np.float32)
pr, pa = pillar()
haze_col = hexc('#f1d5ae')
bim = I.new('L', (W, H), 0); bd = ImageDraw.Draw(bim)
top_line = lambda x: VPY - (VPY - TOP0) * (VPX - x) / (VPX - 360)
bd.polygon([(0, top_line(0) - 160), (W, top_line(W) - 22), (W, top_line(W) + 10), (0, top_line(0) + 95)], fill=255)
uim = I.new('L', (W, H), 0); ud = ImageDraw.Draw(uim)
ud.polygon([(0, top_line(0) + 40), (W, top_line(W) + 3), (W, top_line(W) + 10), (0, top_line(0) + 95)], fill=255)
under = ndi.gaussian_filter(np.asarray(uim, np.float32) / 255, 1.2)
beam = ndi.gaussian_filter(np.asarray(bim, np.float32) / 255, 1.2)
bt = fbm(H, W, 4, 6, seed=3)[..., None] - .5
beam_col = (hexc('#5d4733') * (0.85 + 0.5 * (xx / W))[..., None]) * (1 + .2 * bt)
img = img * (1 - beam[..., None]) + beam_col * beam[..., None]
img = img * (1 - under[..., None]) + (beam_col * 1.55) * under[..., None]

X0 = 360.0
specs = [(.24, 3.2, .62), (.33, 2.6, .5), (.46, 1.8, .34), (.66, 0.6, .14), (1.0, 0.0, 0.03)]
placed = []
for (sc, bl, hz_) in specs:
    x, ty, by = P(sc, X0)
    placed.append((x, ty, sc))
    place(img, cov, pr, pa, x, ty, sc * 1.0, bl, hz_, haze_col)

# festoons between consecutive pillars: jasmine with marigold accents
jim = I.new('L', (W, H), 0); jd = ImageDraw.Draw(jim)
mim = I.new('L', (W, H), 0); md = ImageDraw.Draw(mim)
for (xa, ta, sa), (xb, tb, sb) in zip(placed[1:], placed[:-1]):
    pass
pairs = list(zip(placed[:-1], placed[1:]))
for (x1, t1, s1), (x2, t2, s2) in pairs:
    for k in range(4):
        n = 110
        for i, t in enumerate(np.linspace(0, 1, n)):
            sc = s1 + (s2 - s1) * t
            x = x1 + (x2 - x1) * t
            ybase = t1 + (t2 - t1) * t + 120 * sc
            y = ybase + np.random.default_rng(i * 7 + k).normal(0, 2.5) * sc + (k * 22 + 10) * sc + 230 * sc * 4 * t * (1 - t) * (1 + .22 * k)
            rr_ = max(2.0, (7 - k) * sc * 1.3)
            if k == 1 and i % 12 == 6:
                md.ellipse([x - rr_ * 1.3, y - rr_ * 1.3, x + rr_ * 1.3, y + rr_ * 1.3], fill=255)
            else:
                jd.ellipse([x - rr_, y - rr_ * 1.2, x + rr_, y + rr_ * 1.2], fill=255)
jas = np.asarray(jim, np.float32) / 255; mar = np.asarray(mim, np.float32) / 255
jas = ndi.gaussian_filter(jas, 0.9); mar = ndi.gaussian_filter(mar, 1.0)
jtex = 0.82 + 0.18 * ndi.gaussian_filter(np.random.default_rng(4).random((H, W)).astype(np.float32), 1.5)
img = img * (1 - jas[..., None]) + (hexc('#fbf6ea') * jtex[..., None]) * jas[..., None]
img = img * (1 - mar[..., None]) + (hexc('#e08a1e') * jtex[..., None]) * mar[..., None]
# re-place the nearest pillar so it overlaps its festoon end
x, ty, sc = placed[-1]
place(img, cov, pr, pa, x, ty, sc, 0.0, 0.03, haze_col)

# light shafts from the right-back (sun beyond the hall)
sh = np.zeros((H, W), np.float32)
for c0 in [700, 1000, 1300]:
    sh += np.exp(-(((xx - c0 + (yy - 600) * 0.45) / 60) ** 2))
sh = ndi.gaussian_filter(sh, 28) * (yy > 300)
img = img + sh[..., None] * hexc('#ffe2b0') * 0.10

# floor reflections
mir_src = img.copy()
for yrow in range(int(VPY), H):
    pass
refl = np.zeros_like(img)
# mirror about the local floor line per column (approx: reflect about fy)
yy_i = yy.astype(np.int32)
src_y = np.clip((2 * fy - yy).astype(np.int32), 0, H - 1)
refl = mir_src[src_y, xx.astype(np.int32)]
refl = ndi.gaussian_filter(refl, (10, 2, 0))
fade = np.clip(1 - (yy - fy) / 500, 0, 1)[..., None] * fl[..., None] * 0.38
img = img * (1 - fade) + refl * fade
# bloom + warm grade
lum = img.mean(2)
bloom = ndi.gaussian_filter(np.clip(img - 0.78, 0, None), (24, 24, 0))
img = img + bloom * 0.9
img = img * hexc('#fff3e2')[None, None] ** 0.6
img = vignette(img, .34)
img = grain(img, .018)
img = img / (1 + 0.12 * img)
save(img, 'plate-pillars')
