"""The destination: a Godavari-delta dusk — river, palms, paddy and a glowing wedding mandapam."""
import numpy as np, sys
from scipy import ndimage as ndi
import wc
from wc import Canvas, bezier
from botany import *

OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/site/watercolor/img/destination.webp'
W, H = 1080, 1700
HZ = 760          # horizon
BANK = 1120       # near bank
MX, MB = 700, 1150  # mandapam centre x, base y

wc.seed(51)
cv = Canvas(W, H)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# --- sky: one wet-in-wet graded wash (lilac -> rose -> peach -> gold at the horizon)
sky = cv.gradient_field([(0, '#a998c6'), (0.18, '#c4a3c8'), (0.30, '#e7a6ad'), (0.40, '#f1bf96'), (0.45, '#f5d49a'), (1, '#f5d49a')], warp=30)
skym = np.clip((HZ + 30 - yy) / 40, 0, 1)
cv.wash(skym, sky, opacity=0.62, bleed=10, soft=6, edge=0.25, mottle=0.45, gran=0.35, blooms=3, bloom_size=120)
# drifting indigo cloud bands
for (cy, x0, x1, th) in [(170, -40, 640, 30), (260, 420, 1120, 22), (420, 80, 520, 16), (520, 640, 1100, 12)]:
    band = cv.stroke(bezier((x0, cy), ((x0 + x1) / 2 - 80, cy - 20), ((x0 + x1) / 2 + 80, cy + 18), (x1, cy - 6), 40),
                     th + 10 * np.sin(np.linspace(0, 3, 40)) ** 2)
    cv.wash(band, '#8d86ad', opacity=0.28, bleed=12, soft=8, edge=0.6, mottle=0.5, gran=0.4, local_warp=(14, 18))
# sun: lifted disc with a warm halo
cv.lift(cv.ellipse(380, HZ - 70, 46, 46), amount=0.75, soft=5)
cv.wash(cv.ellipse(380, HZ - 70, 120, 110), '#f3b56f', opacity=0.18, bleed=10, soft=18, edge=0.2)
cv.lift(cv.ellipse(380, HZ - 70, 34, 34), amount=0.85, soft=3)

# --- far shore: pale indigo strip with distant palms
far = np.clip((yy - (HZ - 14)) / 3, 0, 1) * np.clip((HZ + 12 - yy) / 3, 0, 1)
cv.wash(far, '#7d7ea6', opacity=0.32, bleed=5, soft=2.5, edge=0.6, gran=0.5, local_warp=(4, 10))
rng = np.random.default_rng(3)
for k in range(16):
    x = rng.uniform(20, W - 20)
    if 300 < x < 460:
        continue
    palm(cv, x, HZ + 2, rng.uniform(55, 95), lean=rng.uniform(-0.15, 0.15), fronds=9, col='#7b7aa3', op=0.42, scale=0.4)

# --- river: reflection of the sky (flipped), shimmering horizontal lifts
river = np.clip((yy - HZ) / 3, 0, 1) * np.clip((BANK - yy) / 6, 0, 1)
t = np.clip((yy - HZ) / (BANK - HZ), 0, 1)
refl = cv.gradient_field([(0, '#f5d49a'), (0.12, '#f1bf96'), (0.3, '#e3a8b1'), (0.6, '#b4a3c9'), (1, '#97a9c9')], warp=0)
refl_r = np.zeros_like(refl)
for k in range(3):
    col = np.interp(t, [0, .2, .45, .75, 1], [wc.hexrgb(c)[k] for c in ['#f5d49a', '#f0bc98', '#d9a7b8', '#a9a5cb', '#8fa7c6']])
    refl_r[..., k] = ndi.gaussian_filter1d(col, 6, axis=1)
cv.wash(river, refl_r, opacity=0.58, bleed=5, soft=3, edge=0.4, mottle=0.4, gran=0.5)
# sun's reflection column
col = np.exp(-((xx - 380) / 50) ** 2) * river * np.clip((yy - HZ) / 20, 0, 1) * np.exp(-(yy - HZ) / 260)
cv.lift(col, amount=0.55, soft=2)
for k in range(26):
    y = rng.uniform(HZ + 10, BANK - 20)
    x0 = rng.uniform(-50, W)
    L = rng.uniform(60, 260) * (0.5 + (y - HZ) / (BANK - HZ))
    cv.lift(cv.stroke([(x0, y), (x0 + L, y + rng.uniform(-2, 2))], rng.uniform(1.5, 3.5)), amount=0.35, soft=1.2)
for k in range(10):
    y = rng.uniform(HZ + 40, BANK - 10)
    x0 = rng.uniform(-50, W)
    cv.wash(cv.stroke([(x0, y), (x0 + rng.uniform(80, 220), y)], rng.uniform(2, 4)), '#7f88b3', opacity=0.18, bleed=2, soft=1.5, edge=0.4)

# a country boat (Godavari padava) on the water
bx, by = 300, 1035
hull = [(bx - 90, by), (bx - 60, by + 14), (bx + 60, by + 14), (bx + 95, by - 4), (bx + 40, by + 4), (bx - 40, by + 4)]
cv.wash(cv.poly(hull), '#5b4f6a', opacity=0.6, bleed=1, soft=0.6, edge=0.8)
canopy = [(bx - 35, by + 2), (bx - 28, by - 26), (bx + 10, by - 34), (bx + 40, by - 24), (bx + 44, by + 2)]
cv.wash(cv.poly(canopy), '#7a6274', opacity=0.5, bleed=1.2, soft=0.6, edge=0.8)
cv.wash(cv.stroke([(bx + 70, by - 2), (bx + 110, by - 70)], 2.2), '#5b4f6a', opacity=0.5, bleed=0.6, soft=0.5)
cv.wash(cv.stroke([(bx - 90, by + 22), (bx + 90, by + 22)], 5), '#6a6d96', opacity=0.18, bleed=3, soft=3, edge=0.3)

# --- near bank & paddy fields
bankm = np.clip((yy - BANK + 10) / 6, 0, 1)
paddy = cv.gradient_field([(0, '#9fb86a'), (0.75, '#94b462'), (0.85, '#7fa458'), (1, '#6e9a55')], warp=20)
cv.wash(bankm, paddy, opacity=0.42, bleed=6, soft=2, edge=0.7, mottle=0.6, gran=0.7, blooms=2, bloom_size=100)
# shrubs and reeds along the river bank
items = []
for k in range(260):
    x = rng.uniform(-20, W + 20); y = BANK + rng.uniform(-6, 18)
    items.append(([(x, y), (x + rng.uniform(-4, 4), y - rng.uniform(8, 26))], rng.uniform(2, 4)))
cv.wash(cv.strokes(items), '#557a52', opacity=0.42, bleed=1.5, soft=0.8, edge=0.8, gran=0.5)
shr = cv.polys([[(x + 40 * np.cos(t), BANK + 4 + 16 * np.sin(t) - 10) for t in np.linspace(np.pi, 2 * np.pi, 20)] for x in rng.uniform(0, W, 14)])
cv.wash(shr, '#4e6f55', opacity=0.38, bleed=3, soft=1.5, edge=0.9, mottle=0.6)
# field bunds (raised paths) in perspective
for k, yb in enumerate([1235, 1380, 1590]):
    cv.wash(cv.stroke(bezier((-20, yb + 30), (W * 0.3, yb - 25), (W * 0.65, yb + 20), (W + 20, yb - 10), 40), 4 + k * 3), '#c9a66b', opacity=0.28, bleed=2, soft=1, edge=0.6)
# paddy texture: short vertical strokes, denser and larger toward the front
items = []
for c in range(170):
    cy = BANK + 30 + (H - BANK - 30) * rng.uniform(0, 1) ** 0.75
    cx = rng.uniform(0, W)
    depth = (cy - BANK) / (H - BANK)
    s = 8 + depth * 34
    for k in range(int(4 + depth * 5)):
        x = cx + rng.uniform(-1, 1) * s * 0.6
        lean = rng.uniform(-0.5, 0.5) * s
        items.append(([(x, cy), (x + lean * 0.3, cy - s * 0.6), (x + lean, cy - s)], [1.2 + depth * 2, 1 + depth, 0.4]))
cv.wash(cv.strokes(items), '#5f8a4c', opacity=0.36, bleed=0.8, soft=0.5, edge=0.7, gran=0.4)
fg = np.clip((yy - 1450) / 250, 0, 1)
cv.wash(fg, '#6e9a55', opacity=0.25, bleed=10, soft=6, edge=0.1, mottle=0.6, gran=0.6)
# the path that leads to the mandapam ("every road led here")
pathL = bezier((420, H + 20), (470, 1450), (640, 1300), (MX - 20, MB + 8), 50)
pathR = bezier((680, H + 20), (640, 1450), (720, 1300), (MX + 30, MB + 8), 50)
pp = list(map(tuple, pathL)) + list(map(tuple, pathR[::-1]))
cv.lift(cv.poly(pp), amount=0.55, soft=3)
cv.wash(cv.poly(pp), '#e2c48c', opacity=0.25, bleed=3, soft=2, edge=0.8, gran=0.8)

# --- banana plants flanking the mandapam
def banana(x, y, h, flip=1):
    cv.wash(cv.stroke([(x, y), (x + 4 * flip, y - h * 0.55)], 12), '#7f9a55', opacity=0.5, bleed=1, edge=0.8)
    for k, a in enumerate([-2.2, -1.75, -1.3, -0.9, -2.6]):
        a = a if flip > 0 else -np.pi - a
        L = h * (0.55 + 0.1 * (k % 2))
        cx, cy = x + 4 * flip, y - h * 0.5
        p = leaf_poly(cx, cy, L, L * 0.34, a, curve=0.18 * flip)
        cv.wash(cv.poly(p), '#6f9a4c' if k % 2 else '#88ad5a', opacity=0.5, bleed=1.6, soft=0.8, edge=1.0, mottle=0.6, gran=0.5)
        # torn leaf edges: a few lifted slits
        for j in range(3):
            tt = 0.3 + 0.2 * j
            px, py = cx + np.cos(a) * L * tt, cy + np.sin(a) * L * tt
            nrm = (-np.sin(a), np.cos(a))
            cv.lift(cv.stroke([(px, py), (px + nrm[0] * L * 0.17, py + nrm[1] * L * 0.17)], 1.4), amount=0.6, soft=0.6)


banana(MX - 175, MB + 10, 230, flip=-1)
banana(MX + 180, MB + 10, 240, flip=1)

# --- the mandapam
glow_cx, glow_cy = MX, MB - 90
# warm halo around (painted around the light, leaving the centre paper-white)
halo = np.exp(-(((xx - glow_cx) / 260) ** 2 + ((yy - glow_cy) / 190) ** 2))
cv.wash(halo, '#f0a860', opacity=0.5, bleed=12, soft=8, edge=0.0, mottle=0.4, gran=0.2)
core = np.exp(-(((xx - glow_cx) / 120) ** 2 + ((yy - glow_cy) / 90) ** 2))
cv.lift(core, amount=0.6, soft=6)
# platform
plat = [(MX - 140, MB - 6), (MX + 140, MB - 6), (MX + 160, MB + 22), (MX - 160, MB + 22)]
cv.wash(cv.poly(plat), '#b98a6a', opacity=0.5, bleed=1.2, soft=0.6, edge=1.0)
cv.wash(cv.poly([(MX - 160, MB + 12), (MX + 160, MB + 12), (MX + 160, MB + 22), (MX - 160, MB + 22)]), INDIGO, opacity=0.25, bleed=1, soft=0.8)
# four pillars (two front, two back)
for px, op in [(MX - 95, 0.32), (MX + 95, 0.32), (MX - 120, 0.55), (MX + 120, 0.55)]:
    cv.wash(cv.stroke([(px, MB - 6), (px, MB - 165)], 11), '#9a6b55', opacity=op, bleed=0.8, soft=0.5, edge=1.2)
    cv.wash(cv.ellipse(px, MB - 168, 12, 6), OCHRE, opacity=op, bleed=0.6, soft=0.5)
# canopy: tiered roof with a kalasam finial
roof = [(MX - 150, MB - 165), (MX + 150, MB - 165), (MX + 110, MB - 205), (MX + 60, MB - 250), (MX, MB - 268),
        (MX - 60, MB - 250), (MX - 110, MB - 205)]
cv.wash(cv.poly(roof), '#c46a5a', opacity=0.5, bleed=1.4, soft=0.7, edge=1.2, mottle=0.5, gran=0.5)
cv.wash(cv.poly([(MX, MB - 268), (MX + 60, MB - 250), (MX + 110, MB - 205), (MX + 150, MB - 165), (MX + 20, MB - 165)]),
        '#7e4b5c', opacity=0.3, bleed=1.2, soft=1)
cv.wash(cv.poly([(MX - 8, MB - 268), (MX + 8, MB - 268), (MX + 5, MB - 290), (MX, MB - 300), (MX - 5, MB - 290)]), OCHRE, opacity=0.7, bleed=0.6, soft=0.4, edge=1.0)
# jasmine & marigold garlands swagged under the canopy
for sx0, sx1 in [(MX - 150, MX - 50), (MX - 50, MX + 50), (MX + 50, MX + 150)]:
    sw = bezier((sx0, MB - 160), (sx0 + 30, MB - 125), (sx1 - 30, MB - 125), (sx1, MB - 160), 18)
    for k, (x, y) in enumerate(sw):
        if k % 2:
            cv.wash(cv.ellipse(x, y, 5.5, 5), MARI, opacity=0.6, bleed=1, soft=0.4, edge=1.0)
        else:
            cv.wash(cv.ellipse(x, y, 4, 4), '#c9cfd8', opacity=0.25, bleed=0.8, soft=0.3, edge=1.4)
    for x in (sx0,):
        for k in range(8):
            cv.wash(cv.ellipse(x, MB - 155 + k * 12, 4.5, 4.5), MARI if k % 2 else '#cfd3d6', opacity=0.5 if k % 2 else 0.25, bleed=0.8, soft=0.3)
# lamps: tiny lit flames along the platform edge (paper left white, gold halo)
for k in range(7):
    lx = MX - 130 + k * 43
    cv.wash(cv.ellipse(lx, MB - 4, 26, 18), '#f0b25e', opacity=0.25, bleed=3, soft=6, edge=0)
    cv.wash(cv.poly([(lx - 6, MB - 2), (lx + 6, MB - 2), (lx + 4, MB + 4), (lx - 4, MB + 4)]), '#a8743f', opacity=0.6, bleed=0.5, soft=0.4)
    cv.wash(cv.poly([(lx - 2.5, MB - 4), (lx + 2.5, MB - 4), (lx, MB - 16)]), '#f2a04a', opacity=0.65, bleed=0.4, soft=0.4, edge=1.2)

# --- foreground palms (left, framing)
palm(cv, 70, H - 230, 600, lean=0.12, fronds=12, col='#466452', op=0.58, scale=1.3)
palm(cv, 200, BANK + 30, 380, lean=0.18, fronds=11, col='#55735a', op=0.45, scale=0.95)
palm(cv, 990, BANK + 40, 420, lean=-0.12, fronds=10, col='#5a7660', op=0.42, scale=0.9)

# dusk unification glazes: warm light over the land, cool indigo shadow in the foreground
warm = np.clip((yy - BANK + 40) / 60, 0, 1) * np.exp(-((yy - BANK) / 420) ** 2)
cv.wash(warm, '#e8a98a', opacity=0.30, bleed=8, soft=10, edge=0.0, mottle=0.5, gran=0.3)
cool = np.clip((yy - 1350) / 350, 0, 1)
cv.wash(cool, '#6c6f9c', opacity=0.30, bleed=8, soft=10, edge=0.0, mottle=0.5, gran=0.4)
cv.deckle(cx=W / 2, cy=H * 0.5, rx=W * 0.485, ry=H * 0.485, power=4, rough=8)
cv.save(OUT)
print('ok')
