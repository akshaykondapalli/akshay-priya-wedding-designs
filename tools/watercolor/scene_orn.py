"""Invitation thoranam & jasmine garland, kalasam vignette, blessing muggu with deepams, paper tile."""
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
import wc
from wc import Canvas, bezier, petal_poly, leaf_poly
from botany import *

OUT = '/home/claude/site/watercolor/img/'

# ---------- mango-leaf thoranam (top of the invitation) ----------
wc.seed(61)
W, H = 1080, 360
cv = Canvas(W, H)
cord = bezier((-10, 40), (300, 78), (780, 78), (W + 10, 40), 120)
n = 15
for k in range(n):
    i = int(4 + (len(cord) - 9) * k / (n - 1))
    x, y = cord[i]
    L = 150 + 30 * np.sin(k * 1.7) + (25 if k % 2 == 0 else 0)
    a = np.pi / 2 + wc.RNG.uniform(-0.12, 0.12)
    mango_leaf(cv, x, y, L, a)
    if k < n - 1:
        j = int(4 + (len(cord) - 9) * (k + 0.5) / (n - 1))
        mx, my = cord[j]
        marigold(cv, mx, my + 14, 21)
        marigold(cv, mx, my + 52, 16)
cv.wash(cv.stroke(cord, 3), '#8a6a3a', opacity=0.55, bleed=0.8, soft=0.5)
for k in range(n - 1):
    j = int(4 + (len(cord) - 9) * (k + 0.5) / (n - 1))
    mx, my = cord[j]
    cv.wash(cv.ellipse(mx, my + 14, 6, 6), '#b8481f', opacity=0.5, bleed=0.8, soft=0.5)
cv.save(OUT + 'thoranam.webp')

# ---------- jasmine strands with a lotus (bottom of the invitation) ----------
wc.seed(62)
W, H = 1080, 400
cv = Canvas(W, H)
for (y0, sag, sz) in [(150, 120, 15), (110, 170, 13)]:
    for x0, x1 in [(-20, 540), (540, 1100)]:
        sw = bezier((x0, y0), (x0 + 120, y0 + sag), (x1 - 120, y0 + sag), (x1, y0), 70)
        for k, (x, y) in enumerate(sw):
            if k % 2 == 0:
                jasmine_bud(cv, x, y, sz * 1.5, np.pi / 2 + wc.RNG.uniform(-1.2, 1.2))
            else:
                jasmine_flower(cv, x, y, sz * 0.75, petals=5)
for x in (40, 1040):
    jasmine_spray(cv, (x, 400), (x + (120 if x < 500 else -120), 210), n_flowers=4, size=24, leaves=5, bend=0.2 if x < 500 else -0.2)
lotus_pad(cv, 540, 360, 170, 34, rot=1.6)
lotus(cv, 540, 300, 105, open_=1.0)
cv.save(OUT + 'garland.webp')

# ---------- brass kalasam with mango leaves and coconut ----------
wc.seed(63)
W, H = 640, 720
cv = Canvas(W, H)
cx = W / 2
# heap of rice it sits on
heap = [(cx - 220 + 440 * t, 660 - 50 * np.sin(np.pi * t) ** 0.7) for t in np.linspace(0, 1, 40)] + [(cx + 220, 672), (cx - 220, 672)]
cv.wash(cv.poly(heap), '#c8c7c2', opacity=0.25, bleed=2, soft=1, edge=1.2, mottle=0.7, gran=1.0)
items = [([(cx + wc.RNG.uniform(-200, 200), 655 - wc.RNG.uniform(0, 40))] * 2, 3) for _ in range(160)]
items = [([(x, y), (x + 3, y + 1)], 2.2) for (((x, y), _), _) in items]
cv.wash(cv.strokes(items), '#b3ab98', opacity=0.3, bleed=0.4, soft=0.3, edge=0.6)
# pot body
t = np.linspace(0, 1, 60)
prof = 150 * np.sin(np.pi * (0.12 + 0.76 * t)) ** 0.9
body = [(cx - prof[i], 640 - 260 * t[i]) for i in range(60)] + [(cx + prof[i], 640 - 260 * t[i]) for i in range(59, -1, -1)]
cv.wash(cv.poly(body), '#d9a64f', opacity=0.62, bleed=1.4, soft=0.6, edge=1.2, mottle=0.5, gran=0.5)
# shading: right side sienna, left highlight lifted
sh = [(cx + prof[i] * 0.25, 640 - 260 * t[i]) for i in range(60)] + [(cx + prof[i], 640 - 260 * t[i]) for i in range(59, -1, -1)]
cv.wash(cv.poly(sh), '#a65f35', opacity=0.34, bleed=4, soft=14, edge=0.2)
cv.lift(cv.ellipse(cx - 70, 500, 22, 70), amount=0.55, soft=6)
# neck and rim
cv.wash(cv.poly([(cx - 70, 382), (cx + 70, 382), (cx + 60, 350), (cx - 60, 350)]), '#cf9a45', opacity=0.6, bleed=1, soft=0.6, edge=1.0)
cv.wash(cv.ellipse(cx, 350, 92, 18), '#b77b38', opacity=0.6, bleed=1, soft=0.5, edge=1.2)
# turmeric band and kumkum dots on the pot
cv.wash(cv.stroke([(cx - 140, 520), (cx, 532), (cx + 140, 520)], 10), '#e7b931', opacity=0.5, bleed=1, soft=0.6)
for dx in (-90, -45, 0, 45, 90):
    cv.wash(cv.ellipse(cx + dx, 470 + abs(dx) * 0.05, 9, 9), '#c2263c', opacity=0.7, bleed=0.8, soft=0.5, edge=1.2)
# mango leaves fanning from the mouth
for k in range(9):
    a = -np.pi / 2 + (k / 8 - 0.5) * 2.6
    leaf(cv, cx + np.cos(a) * 40, 352 + np.sin(a) * 6, 175, 44, a, col='#6e9a48' if k % 2 else '#86ab55', op=0.58, curve=0.08)
# coconut (blot the leaves where it sits, then paint it)
cv.lift(cv.ellipse(cx, 300, 62, 70), amount=0.85, soft=2)
cv.wash(cv.ellipse(cx, 300, 64, 72), '#8a6a42', opacity=0.6, bleed=1.4, soft=0.7, edge=1.1, mottle=0.6, gran=0.8)
cv.wash(cv.ellipse(cx + 18, 306, 40, 60), '#5d4630', opacity=0.35, bleed=2, soft=4, edge=0.4)
fib = [([(cx + wc.RNG.uniform(-50, 40), 250 + wc.RNG.uniform(0, 90)), None], 0) for _ in range(40)]
fib = [([(x, y), (x + wc.RNG.uniform(-6, 6), y + wc.RNG.uniform(8, 18))], 1.2) for (((x, y), _), _) in fib]
cv.wash(cv.strokes(fib), '#4f3a28', opacity=0.35, bleed=0.4, soft=0.3)
cv.wash(cv.poly([(cx - 8, 232), (cx + 8, 232), (cx, 210)]), '#6b4f33', opacity=0.6, bleed=0.6, soft=0.4)
cv.wash(cv.ellipse(cx, 268, 10, 10), '#c2263c', opacity=0.7, bleed=0.6, soft=0.4, edge=1.2)
cv.save(OUT + 'kalasam.webp')

# ---------- blessing: lotus muggu with two lit deepams ----------
wc.seed(64)
W, H = 1080, 980
cv = Canvas(W, H)
cx, cy = W / 2, 560
# muggu: dot grid + 8-petal lotus + interlaced loops, drawn in rice white over a turmeric-rose ground
ground = cv.ellipse(cx, cy, 430, 300)
cv.wash(ground, '#e8b6a2', opacity=0.12, bleed=12, soft=10, edge=0.6, mottle=0.6, gran=0.6, blooms=2, bloom_size=90)
lines = []
for k in range(8):
    a = k * np.pi / 4
    p = petal_poly(cx, cy, 250, 120, a, n=40)
    lines.append((p + [p[0]], 4.2))
    p2 = petal_poly(cx, cy, 160, 70, a + np.pi / 8, n=30)
    lines.append((p2 + [p2[0]], 3.6))
for rr in (60,):
    ts = np.linspace(0, 2 * np.pi, 120)
    lines.append(([(cx + rr * np.cos(t), cy + rr * 0.7 * np.sin(t) / 0.7 * 0.7 / 0.7 * (0.68)) for t in ts], 3.4))
# flatten to perspective (muggu seen on the ground)
def persp(pts):
    return [(cx + (x - cx), cy + (y - cy) * 0.55) for x, y in pts]
lines = [(persp(p), w) for p, w in lines]
mug = cv.strokes(lines)
cv.wash(mug, '#c77a58', opacity=0.55, bleed=1, soft=0.6, edge=1.2, gran=0.8)
# petal fills in rose and turmeric
for k in range(8):
    a = k * np.pi / 4
    p = persp(petal_poly(cx, cy, 240, 100, a, n=40))
    cv.wash(cv.poly(p), '#e6879c' if k % 2 else '#eab84e', opacity=0.22, bleed=2, soft=1, edge=1.0, gran=0.7)
dots = []
for k in range(16):
    a = k * np.pi / 8 + np.pi / 16
    for rr in (205, 330):
        x, y = cx + rr * np.cos(a), cy + rr * np.sin(a) * 0.55
        dots.append(('ell', (x - 6, y - 4, x + 6, y + 4)))
cv.wash(cv._draw(dots), '#a5563f', opacity=0.6, bleed=0.6, soft=0.5, edge=1.0)


def deepam(x, y, s):
    # glow first (painted around the flame)
    cv.wash(cv.ellipse(x + 40 * s, y - 120 * s, 120 * s, 130 * s), '#f2b066', opacity=0.22, bleed=8, soft=20, edge=0, mottle=0.2)
    cv.lift(cv.ellipse(x + 46 * s, y - 120 * s, 40 * s, 60 * s), amount=0.5, soft=10)
    base = [(x - 80 * s, y), (x + 80 * s, y), (x + 55 * s, y - 22 * s), (x - 55 * s, y - 22 * s)]
    cv.wash(cv.poly(base), '#cf9844', opacity=0.6, bleed=1, soft=0.6, edge=1.1)
    cv.wash(cv.stroke([(x, y - 20 * s), (x, y - 70 * s)], 22 * s), '#c58c3e', opacity=0.6, bleed=1, soft=0.6, edge=1.1)
    for yy_ in (-34, -52):
        cv.wash(cv.ellipse(x, y + yy_ * s, 18 * s, 6 * s), '#a8692f', opacity=0.5, bleed=0.6, soft=0.5)
    bowl = [(x - 70 * s + 140 * s * t, y - 78 * s + 26 * s * np.sin(np.pi * t)) for t in np.linspace(0, 1, 30)]
    cv.wash(cv.poly(bowl + [(x + 70 * s, y - 82 * s), (x - 70 * s, y - 82 * s)]), '#d9a64f', opacity=0.65, bleed=1, soft=0.6, edge=1.2)
    cv.wash(cv.ellipse(x, y - 82 * s, 70 * s, 10 * s), '#a8692f', opacity=0.55, bleed=0.8, soft=0.5, edge=1.0)
    cv.lift(cv.ellipse(x - 30 * s, y - 70 * s, 10 * s, 5 * s), amount=0.6, soft=2)
    # flame
    fl = petal_poly(x + 46 * s, y - 86 * s, 70 * s, 26 * s, -np.pi / 2 - 0.05, tip=0.3)
    cv.wash(cv.poly(fl), '#f3b346', opacity=0.55, bleed=1, soft=1.2, edge=1.4)
    inner = petal_poly(x + 46 * s, y - 88 * s, 34 * s, 12 * s, -np.pi / 2, tip=0.3)
    cv.wash(cv.poly(inner), '#e0712f', opacity=0.35, bleed=0.8, soft=1.2, edge=0.6)


deepam(170, 760, 1.55)
deepam(860, 760, 1.55)
# a few fallen jasmine flowers and marigold petals
for (x, y) in [(400, 820), (690, 840), (540, 300), (180, 470), (900, 470), (560, 880)]:
    jasmine_flower(cv, x, y, 22)
for (x, y) in [(360, 360), (730, 350), (470, 860), (620, 800), (130, 760), (960, 770)]:
    cv.wash(cv.poly(petal_poly(x, y, 20, 12, wc.RNG.uniform(0, 6))), MARI, opacity=0.5, bleed=1, soft=0.5, edge=1.0)
cv.deckle(cx=W / 2, cy=H * 0.55, rx=W * 0.56, ry=H * 0.52, power=3, rough=7)
cv.save(OUT + 'blessing.webp')
print('ok')
