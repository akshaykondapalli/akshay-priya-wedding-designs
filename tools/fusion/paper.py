"""Handmade paper with soft watercolor blooms at the corners (invitation & details background)."""
from common import *
S = 1600; H = W = S
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
ph = fbm(H, W, 6, 3, seed=401) * 0.6 + fbm(H, W, 30, 3, seed=402) * 0.4
gy, gx = np.gradient(ndi.gaussian_filter(ph, 1.0))
paper = np.array([0.972, 0.948, 0.900]) * (0.975 + 0.04 * (1 + (gx - gy) * 6))[..., None]
# fibres
r = np.random.default_rng(403)
fib = np.zeros((H, W), np.float32)
for i in range(500):
    x0, y0 = r.uniform(0, W), r.uniform(0, H)
    a = r.uniform(0, np.pi); L_ = r.uniform(10, 40)
    for t in np.linspace(0, 1, 20):
        xi, yi = int(x0 + np.cos(a) * L_ * t), int(y0 + np.sin(a) * L_ * t + 6 * np.sin(t * 3))
        if 0 <= xi < W and 0 <= yi < H:
            fib[yi, xi] = 1
fib = ndi.gaussian_filter(fib, 0.6)
paper = paper * (1 - fib[..., None] * 0.08)

def glaze(base, pig, d):
    d = np.clip(d, 0, 1)[..., None]
    return base * (1 - d) + base * pig * d

def wash(cx, cy, rad, pig, den, seed):
    d = np.sqrt(((x - cx) / rad) ** 2 + ((y - cy) / rad) ** 2) + (fbm(H, W, 120, 4, seed=seed) - .5) * 0.7
    reg = smoothstep(1.0, 0.92, d)
    edge = np.exp(-((d - 0.96) / 0.02) ** 2)
    inner = reg * (0.5 + 0.5 * fbm(H, W, 60, 3, seed=seed + 1))
    return den * inner + den * 1.4 * edge * reg.max()

col = paper
col = glaze(col, np.array([0.93, 0.70, 0.66]), wash(0, 0, 520, None, 0.28, 410))
col = glaze(col, np.array([0.70, 0.82, 0.74]), wash(-60, 360, 420, None, 0.22, 420))
col = glaze(col, np.array([0.98, 0.82, 0.60]), wash(W, H, 560, None, 0.26, 430))
col = glaze(col, np.array([0.62, 0.78, 0.78]), wash(W + 40, H - 420, 380, None, 0.2, 440))
col = glaze(col, np.array([0.95, 0.76, 0.70]), wash(W - 80, 60, 260, None, 0.16, 450))
col = glaze(col, np.array([0.75, 0.84, 0.72]), wash(120, H - 60, 300, None, 0.16, 460))
col += grain(H, W, 0.01, seed=470)
save(col, 'paper.webp', q=76)
save(col, 'paper-900.webp', q=74, size=(900, 900))
