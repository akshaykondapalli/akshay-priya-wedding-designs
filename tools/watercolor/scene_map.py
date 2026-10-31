"""Imaginary painted map + two pigment paths (separate layers) + the meeting bloom."""
import numpy as np, json, sys
import wc
from wc import Canvas, bezier
from botany import *

OUT = '/home/claude/site/watercolor/img/'
W, H = 1080, 1500
J = (590, 860)   # where the two journeys meet

wc.seed(21)
cv = Canvas(W, H)


def blob(cx, cy, r, n=90, rough=0.28, seed_=0):
    rng = np.random.default_rng(seed_)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rad = np.ones(n)
    for k, amp in [(2, .18), (3, .14), (5, .10), (9, .06), (17, .035)]:
        rad += amp * rough / .28 * np.sin(k * t + rng.uniform(0, 6.28))
    return [(cx + r[0] * rad[i] * np.cos(t[i]), cy + r[1] * rad[i] * np.sin(t[i])) for i in range(n)]


lands = [
    blob(250, 330, (230, 170), seed_=1),       # north-western isle
    blob(840, 1180, (230, 200), seed_=2),      # south-eastern isle
    blob(600, 830, (210, 160), seed_=3),       # the meeting land (centre)
    blob(900, 380, (120, 90), seed_=4),
    blob(170, 1150, (110, 130), seed_=5),
    blob(470, 560, (40, 28), seed_=6), blob(760, 640, (34, 24), seed_=7), blob(380, 1050, (30, 22), seed_=8),
]
land = cv.polys(lands)

# sea: graded cerulean glaze everywhere except land, dark wet edge along coasts
sea_field = cv.gradient_field([(0, '#8fbfd9'), (0.5, '#7fb4d3'), (1, '#9cc6d6')], warp=30)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
area = np.clip(1 - (((xx - W / 2) / (W * .56)) ** 4 + ((yy - H / 2) / (H * .52)) ** 4), 0, 1)
area = np.clip(area * 6, 0, 1)
from scipy import ndimage as ndi
sea = np.clip(area - ndi.gaussian_filter(land, 2), 0, 1)
cv.wash(sea, sea_field, opacity=0.30, bleed=6, soft=2, edge=1.4, edge_width=6, mottle=0.55, gran=0.9, blooms=3, bloom_size=110)
# coastal shallows: second, narrower glaze following the coastlines
coast = np.clip(ndi.gaussian_filter(land, 16) * 2.2 - land * 1.5, 0, 1) * area
cv.wash(coast, '#5f9fc4', opacity=0.12, bleed=4, soft=6, edge=0.2, gran=0.6)

# land: yellow ochre ground, sap-green interior
cv.wash(land, '#e6c58a', opacity=0.28, bleed=2.5, soft=1, edge=0.8, mottle=0.6, gran=0.5)
inner = np.clip(ndi.gaussian_filter(land, 20) * 1.8 - 0.75, 0, 1)
cv.wash(inner, '#a9bd72', opacity=0.30, bleed=8, soft=6, edge=0.4, mottle=0.7, gran=0.7, blooms=2, bloom_size=50)

# little painted hills & palms on the lands (symbolic, unlabeled)
rng = np.random.default_rng(5)
for (cx, cy, rx, ry) in [(250, 330, 150, 100), (840, 1180, 150, 120), (600, 830, 130, 90)]:
    for k in range(7):
        hx = cx + rng.uniform(-rx, rx) * 0.8
        hy = cy + rng.uniform(-ry, ry) * 0.7
        s = rng.uniform(16, 30)
        if land[int(hy), int(hx)] < 0.5:
            continue
        hill = [(hx - s, hy), (hx - s * 0.2, hy - s * 0.9), (hx + s * 0.3, hy - s * 0.7), (hx + s, hy)]
        cv.wash(cv.poly(hill), '#8a9e6a', opacity=0.35, bleed=1.2, soft=0.6, edge=1.0)
        cv.wash(cv.poly([(hx - s * 0.2, hy - s * 0.9), (hx + s * 0.3, hy - s * 0.7), (hx + s, hy), (hx + s * 0.1, hy)]),
                INDIGO, opacity=0.14, bleed=1, soft=0.8, edge=0.6)

# graticule: faint sienna pencil-like lines
for gx in range(90, W, 180):
    cv.wash(cv.stroke([(gx, 60), (gx + 8, H - 60)], 1.1), SIENNA, opacity=0.10, bleed=0.6, soft=0.4, edge=0.2, gran=0.9)
for gy in range(120, H, 200):
    cv.wash(cv.stroke([(50, gy), (W - 50, gy - 6)], 1.1), SIENNA, opacity=0.10, bleed=0.6, soft=0.4, edge=0.2, gran=0.9)

# compass rose (bottom-left)
ccx, ccy, R = 190, 1340, 70
pts = []
for k in range(8):
    a = k * np.pi / 4 - np.pi / 2
    L = R if k % 2 == 0 else R * 0.55
    pts.append([(ccx, ccy), (ccx + np.cos(a - .2) * L * .25, ccy + np.sin(a - .2) * L * .25), (ccx + np.cos(a) * L, ccy + np.sin(a) * L)])
    pts.append([(ccx, ccy), (ccx + np.cos(a + .2) * L * .25, ccy + np.sin(a + .2) * L * .25), (ccx + np.cos(a) * L, ccy + np.sin(a) * L)])
cv.wash(cv.polys(pts[0::2]), INDIGO, opacity=0.35, bleed=0.8, soft=0.5, edge=0.6)
cv.wash(cv.polys(pts[1::2]), OCHRE, opacity=0.35, bleed=0.8, soft=0.5, edge=0.6)
ring = cv.ellipse(ccx, ccy, R * .75, R * .75) - cv.ellipse(ccx, ccy, R * .70, R * .70)
cv.wash(np.clip(ring, 0, 1), INDIGO, opacity=0.25, bleed=0.6, soft=0.4, edge=0.3)

cv.deckle(cx=W / 2, cy=H / 2, rx=W * .48, ry=H * .48, power=4, rough=7)
cv.save(OUT + 'map.webp')

# ---------- the two journeys (each its own layer, revealed by an SVG mask) ----------
def catmull(pts, per=40):
    pts = np.asarray(pts, np.float32)
    pts = np.vstack([pts[0], pts, pts[-1]])
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-2])
    return np.array(out)


rose_path = catmull([(185, 300), (320, 235), (395, 400), (290, 520), (350, 660), (470, 700), (J[0] - 8, J[1] - 14)])
blue_path = catmull([(885, 1245), (740, 1300), (650, 1170), (800, 1060), (850, 960), (720, 960), (J[0] + 8, J[1] + 8)])


def paint_path(path, pig, pig_d, fname, seed_):
    wc.seed(seed_)
    c2 = Canvas(W, H)
    n = len(path)
    widths = 7 + 3 * np.sin(np.linspace(0, 9, n)) + np.linspace(2, 0, n)
    m = c2.stroke(path, widths)
    c2.wash(m, pig, opacity=0.62, bleed=1.6, soft=0.7, edge=1.4, mottle=0.5, gran=0.8)
    # pigment pooling: darker dots where the brush paused
    rng = np.random.default_rng(seed_)
    for i in rng.choice(np.arange(15, n - 10), 5, replace=False):
        x, y = path[i]
        c2.wash(c2.ellipse(x, y, rng.uniform(6, 10), rng.uniform(5, 8)), pig_d, opacity=0.35, bleed=2, soft=1, edge=1.0)
    # origin: a small painted ring
    x, y = path[0]
    c2.wash(c2.ellipse(x, y, 20, 20), pig, opacity=0.5, bleed=2, soft=1, edge=1.5, blooms=1, bloom_size=10)
    c2.save(OUT + fname)


paint_path(rose_path, '#d9718c', '#b84a6b', 'path-rose.webp', 31)
paint_path(blue_path, '#5d9ccc', '#3b74a8', 'path-blue.webp', 32)

# ---------- the meeting bloom: rose + cerulean meet wet-in-wet, blending into dusk lilac ----------
wc.seed(41)
B = 1080
cb = Canvas(B, B)
yy, xx = np.mgrid[0:B, 0:B].astype(np.float32)
ang = np.arctan2(yy - B / 2, xx - B / 2)
field = np.zeros((B, B, 3), np.float32)
rose = wc.hexrgb('#ea9db0'); blue = wc.hexrgb('#94bfe0'); lilac = wc.hexrgb('#d2b6dc'); gold = wc.hexrgb('#f5d29a')
tmix = (np.sin(ang + 0.6) * 0.5 + 0.5)[..., None]
d = (np.sqrt((xx - B / 2) ** 2 + (yy - B / 2) ** 2) / (B / 2))[..., None]
field = rose * tmix + blue * (1 - tmix)
field = field * np.clip(d * 1.4, 0, 1) + lilac * (1 - np.clip(d * 1.4, 0, 1))
centre = np.exp(-(d[..., 0] / 0.32) ** 2)[..., None]
field = field * (1 - centre) + gold * centre
for k in range(3):
    field[..., k] = ndi.gaussian_filter(cb.warp(field[..., k], 25), 6)
bl = cb.ellipse(B / 2, B / 2, B * .40, B * .40)
cb.wash(bl, field, opacity=0.46, bleed=9, soft=10, edge=1.1, edge_width=18, mottle=0.35, gran=0.35, blooms=3, bloom_size=150, local_warp=(30, 40))
cb.wash(cb.ellipse(B / 2, B / 2, B * .22, B * .22), field, opacity=0.22, bleed=8, soft=12, edge=0.9, edge_width=12, gran=0.3, blooms=2, bloom_size=70, local_warp=(25, 30))
cb.save(OUT + 'bloom.webp')

json.dump({'W': W, 'H': H, 'J': J,
           'rose': [[round(float(x), 1), round(float(y), 1)] for x, y in rose_path],
           'blue': [[round(float(x), 1), round(float(y), 1)] for x, y in blue_path]},
          open('/home/claude/tools/watercolor/paths.json', 'w'))
print('ok')
