"""Endpaper: cream laid paper printed with a faded teal muggu lattice."""
from common import *
EW, EH = 700, 980
ey, ex = np.mgrid[0:EH, 0:EW].astype(np.float32)
# muggu: dot grid + two families of diagonal lines that weave (sine) around the dots
cell = 56
dots = ''.join(f'<circle cx="{i*cell}" cy="{j*cell}" r="3"/>' for j in range(-1, EH//cell+2) for i in range(-1, EW//cell+2))
import math
paths = []
L = (EW + EH) * 1.5
step = cell * math.sqrt(2)
for sgn in (1, -1):
    for k in range(-60, 60):
        # line through (k+0.5)*cell offset, direction (1, sgn)/sqrt2
        ox, oy = (k + 0.5) * cell, 0
        pts = []
        for t in np.arange(-L, L, 4):
            px = ox + t / math.sqrt(2)
            py = oy + sgn * t / math.sqrt(2)
            off = cell * 0.16 * math.sin(2 * math.pi * t / step)
            px += -sgn * off / math.sqrt(2); py += off / math.sqrt(2)
            if -20 < px < EW + 20 and -20 < py < EH + 20:
                pts.append(f'{px:.1f},{py:.1f}')
        if len(pts) > 2:
            paths.append('<polyline points="' + ' '.join(pts) + '"/>')
loops = ''.join(paths)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{EW}" height="{EH}">
<g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">{loops}</g><g fill="#fff">{dots}</g></svg>'''
m = render_svg(svg, EW, EH, 'endmask', transparent=True)[..., 3]
paper = np.array([0.93, 0.89, 0.80])
laid = 0.015 * np.sin(ex * 2 * np.pi / 6) + 0.03 * np.exp(-((ex % 140) - 70) ** 2 / 2)
tex = 0.9 + 0.1 * fbm(EH, EW, 3, 2, seed=61) + laid - 0.06 * (fbm(EH, EW, 200, 3, seed=62) - .5)
col = paper * tex[..., None]
ink = np.array([0.14, 0.36, 0.34])
inkcov = (m * (0.55 + 0.35 * fbm(EH, EW, 50, 3, seed=63)))[..., None]
col = col * (1 - inkcov) + ink * inkcov
col *= (1 - 0.40 * np.exp(-((EW - ex) / 45) ** 2))[..., None]
col += grain(EH, EW, 0.012, seed=64)
save(col, 'endpaper.webp', q=78)
