"""Frontispiece: a lotus pond vignette framed by arching jasmine sprays."""
import numpy as np, sys
import wc
from wc import Canvas
from botany import *

wc.seed(11)
W, H = 1080, 1500
cv = Canvas(W, H)

# soft ground washes (wet-in-wet sky glow behind the arrangement)
sky = cv.gradient_field([(0, '#f3d9c4'), (0.45, '#f6e2cf'), (0.7, '#cfe2e6'), (1, '#b7d4dc')], warp=40)
m = cv.ellipse(W / 2, H * 0.70, W * 0.50, H * 0.30)
cv.wash(m, sky, opacity=0.55, bleed=14, soft=10, edge=0.5, mottle=0.5, gran=0.35, blooms=2, bloom_size=90)

# pond water — cerulean with horizontal reflections
water = cv.ellipse(W / 2, H * 0.86, W * 0.55, H * 0.13)
cv.wash(water, CERU, opacity=0.26, bleed=12, soft=6, edge=0.6, mottle=0.6, gran=0.6, blooms=1, bloom_size=80)
for k in range(5):
    y = H * (0.79 + 0.018 * k) + wc.RNG.uniform(-6, 6)
    x0 = W * wc.RNG.uniform(0.12, 0.4)
    x1 = W * wc.RNG.uniform(0.6, 0.9)
    cv.wash(cv.stroke([(x0, y), (x1, y + wc.RNG.uniform(-4, 4))], wc.RNG.uniform(2, 5)), '#5f93b8',
            opacity=0.14, bleed=3, soft=2.5, edge=0.4)

# lotus pads
lotus_pad(cv, W * 0.30, H * 0.86, 150, 44, rot=0.3)
lotus_pad(cv, W * 0.73, H * 0.88, 175, 50, rot=2.7)
lotus_pad(cv, W * 0.55, H * 0.94, 110, 28, rot=1.5)

# lotus stems + flowers
for (x, y, s, o) in [(W * 0.43, H * 0.69, 140, 1.0), (W * 0.65, H * 0.745, 100, 0.75)]:
    stem(cv, bezier((x, y + 20), (x + 6, y + 90), (x - 8, y + 150), (x + 4, H * 0.86), 30), w=6, col='#6f8f58', op=0.45)
    lotus(cv, x, y, s, open_=o)
# a bud
bx, by = W * 0.24, H * 0.73
stem(cv, bezier((bx, by + 10), (bx - 5, by + 80), (bx + 6, by + 130), (bx, H * 0.86), 30), w=5, col='#6f8f58', op=0.45)
cv.wash(cv.poly(petal_poly(bx, by + 18, 70, 36, -np.pi / 2, tip=0.4)), ROSE, opacity=0.45, bleed=1.5, edge=1.0)
cv.wash(cv.poly(petal_poly(bx, by - 5, 45, 26, -np.pi / 2, tip=0.4)), ROSE_D, opacity=0.35, bleed=1.5, soft=2, edge=0.6)

# jasmine sprays arching up from both lower corners, framing the empty upper page
jasmine_spray(cv, (W * 0.02, H * 0.98), (W * 0.30, H * 0.42), n_flowers=9, size=38, leaves=11, bend=0.35)
jasmine_spray(cv, (W * 0.98, H * 0.97), (W * 0.72, H * 0.40), n_flowers=9, size=38, leaves=11, bend=-0.35)
jasmine_spray(cv, (W * 0.10, H * 1.0), (W * 0.06, H * 0.55), n_flowers=5, size=32, leaves=7, bend=-0.2)
jasmine_spray(cv, (W * 0.90, H * 1.0), (W * 0.95, H * 0.58), n_flowers=5, size=32, leaves=7, bend=0.2)

# fade lower edge irregularly into paper
cv.deckle(cx=W / 2, cy=H * 0.56, rx=W * 0.485, ry=H * 0.43, power=3.5, rough=6)
out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/site/watercolor/img/frontispiece.webp'
cv.save(out)
print('ok', out)
