"""Imaginary hand-painted watercolor atlas map (unlabeled, symbolic)."""
from common import *
import json

S = 1800
H = W = S
y, x = np.mgrid[0:H, 0:W].astype(np.float32)

# ---------- paper ----------
ph = fbm(H, W, 7, 3, seed=101) * 0.6 + fbm(H, W, 40, 3, seed=102) * 0.4
gy, gx = np.gradient(ndi.gaussian_filter(ph, 1.0))
paper_light = 1 + (gx - gy) * 6
paper = np.array([0.955, 0.925, 0.86]) * (0.97 + 0.05 * paper_light[..., None])
paper *= (1 - 0.05 * (fbm(H, W, 400, 3, seed=103) - 0.5))[..., None]

# ---------- land ----------
def bump(cx, cy, sx, sy, a=1):
    return a * np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))

field = (fbm(H, W, 380, 5, seed=111) - 0.5) * 0.9 + (fbm(H, W, 110, 5, 0.55, seed=119) - 0.5) * 0.55
field += bump(150, 520, 520, 480, 0.95)      # north-west land (journey one)
field += bump(1700, 1320, 520, 520, 0.95)    # south-east land (journey two)
field += bump(940, 720, 380, 300, 0.9)     # central land
field += bump(930, 1060, 140, 230, 0.75)    # central peninsula tip pointing south (destination)
field += bump(1450, 330, 160, 120, 0.55)     # small north-east isles
field += bump(380, 1420, 150, 110, 0.5)      # small south-west isle
field -= bump(560, 900, 160, 260, 0.6)       # keep a channel between W land and centre
field -= bump(1250, 1040, 150, 260, 0.6)
land = field > 0.52
land = ndi.binary_opening(land, iterations=3)
land = ndi.binary_fill_holes(land)
lab, n = ndi.label(land)
sizes = ndi.sum(land, lab, range(1, n + 1))
for i, s_ in enumerate(sizes):
    if s_ < 1500:
        land[lab == i + 1] = False
landf = land.astype(np.float32)
# wobble edges like a painted wash
wob = (fbm(H, W, 18, 3, seed=112) - 0.5)
landw = ndi.gaussian_filter(landf, 2.5) + wob * 0.25 > 0.5
landw = landw.astype(np.float32)

dist_in = ndi.distance_transform_edt(landw)
dist_out = ndi.distance_transform_edt(1 - landw)

# ---------- watercolor layering helper (subtractive-ish) ----------
def glaze(base, pigment, density):
    """Kubelka-Munk-lite: multiply toward pigment color by density."""
    d = np.clip(density, 0, 1.2)[..., None]
    return base * (1 - d) + base * pigment * d


granul = smoothstep(0.35, 0.75, fbm(H, W, 3, 2, seed=120)) * 0.6 + smoothstep(0.3, 0.8, ph) * 0.4
col = paper.copy()

# sea: wet-in-wet teal-blue, darker near the coast, fading out toward open sea
sea = 1 - landw
seavar = fbm(H, W, 260, 4, seed=121)
coast_band = np.exp(-dist_out / 70)
sea_den = sea * (0.20 + 0.28 * seavar + 0.32 * coast_band) * (0.85 + 0.3 * granul)
sea_col = np.array([0.55, 0.76, 0.80])
col = glaze(col, sea_col, sea_den)
# second sea glaze, deeper teal, patchy
deep = sea * smoothstep(0.55, 0.85, fbm(H, W, 200, 4, seed=122)) * 0.35 * (1 - coast_band * 0.5)
col = glaze(col, np.array([0.38, 0.62, 0.66]), deep)
# hard pigment edge at the sea/coast boundary (edge darkening)
sea_edge = sea * np.exp(-dist_out / 5) * 0.35
col = glaze(col, np.array([0.40, 0.62, 0.68]), sea_edge)

def hard_wash(col, n, thr, pigment, den, mask, edge_den=0.5, seed=0):
    reg = smoothstep(thr, thr + 0.012, n) * mask
    e = np.abs(np.gradient(ndi.gaussian_filter(reg, 1.2))[0]) + np.abs(np.gradient(ndi.gaussian_filter(reg, 1.2))[1])
    e = np.clip(e * 3.5, 0, 1)
    col = glaze(col, pigment, reg * den)
    return glaze(col, pigment, e * edge_den)

# visible hard-edged wash passes in the sea
for i, (thr, den) in enumerate([(0.56, 0.14), (0.6, 0.10)]):
    n_ = fbm(H, W, 520 - i * 120, 4, 0.42, seed=125 + i)
    col = hard_wash(col, n_, thr, np.array([0.50, 0.70, 0.76]), den, sea * (1 - np.exp(-dist_out / 25)), 0.22)

# land washes: ochre + sage + touches of rose earth
lv1 = fbm(H, W, 220, 4, seed=131)
lv2 = fbm(H, W, 120, 4, seed=132)
ochre = np.array([0.93, 0.80, 0.56]); sage = np.array([0.70, 0.80, 0.62]); rose = np.array([0.93, 0.74, 0.68])
land_tint = ochre[None, None] * (1 - lv1[..., None]) + sage[None, None] * lv1[..., None]
land_tint = land_tint * (1 - 0.35 * smoothstep(0.65, 0.85, lv2)[..., None]) + rose * 0.35 * smoothstep(0.65, 0.85, lv2)[..., None]
land_den = landw * (0.45 + 0.25 * fbm(H, W, 90, 3, seed=133)) * (0.85 + 0.3 * granul)
col = glaze(col, land_tint, land_den)
for i, (thr, pig, den) in enumerate([(0.55, np.array([0.70, 0.80, 0.58]), 0.30), (0.63, np.array([0.92, 0.72, 0.62]), 0.18)]):
    n_ = fbm(H, W, 300 - i * 80, 4, 0.45, seed=135 + i)
    col = hard_wash(col, n_, thr, pig, den, landw, 0.3)
# pigment pooling along the inside of the coastline
pool = landw * (np.exp(-dist_in / 6) * 0.55 + np.exp(-dist_in / 30) * 0.15)
col = glaze(col, np.array([0.78, 0.62, 0.42]), pool)
# blooms (back-runs): cauliflower rings
r_ = np.random.default_rng(140)
bloom = np.zeros((H, W), np.float32)
for i in range(16):
    bx, by = r_.integers(100, W - 100), r_.integers(100, H - 100)
    if not land[by, bx]:
        continue
    rr = r_.integers(40, 110)
    d = np.sqrt((x - bx) ** 2 + (y - by) ** 2) + (fbm(H, W, 20, 2, seed=150 + i) - .5) * 30
    bloom += np.exp(-((d - rr) / 4) ** 2) * 0.35 - (d < rr) * 0.10
col = glaze(col, np.array([0.80, 0.68, 0.50]), np.clip(bloom, -0.2, 1) * landw)
# hill shadows: soft sage-blue washes in the interior
hills = landw * smoothstep(0.6, 0.85, fbm(H, W, 70, 3, seed=160)) * smoothstep(20, 80, dist_in)
col = glaze(col, np.array([0.62, 0.70, 0.66]), hills * 0.4)

# ---------- ink layer (SVG): coastline ripples, mountains, trees, graticule, compass ----------
from skimage import measure
contours = measure.find_contours(ndi.gaussian_filter(landw, 1.5), 0.5)
paths = []
for c in contours:
    if len(c) < 80:
        continue
    c = c[::3]
    d = 'M' + ' L'.join(f'{p[1]:.1f} {p[0]:.1f}' for p in c) + 'Z'
    paths.append(d)
coast_svg = ''.join(f'<path d="{d}"/>' for d in paths)
# offshore ripple lines: contours of distance field outside land
ripples = ''
for k, dd in enumerate([14, 30, 52]):
    cs = measure.find_contours(ndi.gaussian_filter(dist_out, 2), dd)
    for c in cs:
        if len(c) < 120:
            continue
        c = c[::4]
        ripples += f'<path d="M{" L".join(f"{p[1]:.1f} {p[0]:.1f}" for p in c)}" opacity="{0.55 - k*0.15:.2f}"/>'

r2 = np.random.default_rng(170)
marks = ''
# mountains
cand = np.argwhere((dist_in > 45) & (fbm(H, W, 70, 3, seed=160) > 0.55))
r2.shuffle(cand)
placed = []
for (py, px) in cand[:4000]:
    if len(placed) > 70:
        break
    if any((px - qx) ** 2 + (py - qy) ** 2 < 55 ** 2 for qx, qy in placed):
        continue
    placed.append((px, py))
    s = r2.uniform(18, 30)
    marks += (f'<path class="m" d="M{px-s} {py} L{px-s*0.15} {py-s*0.95} L{px+s*0.2} {py-s*0.55} L{px+s*0.45} {py-s*0.8} L{px+s} {py}"/>'
              f'<path class="ms" d="M{px-s*0.15} {py-s*0.95} L{px+s*0.05} {py} L{px+s*0.2} {py-s*0.55}"/>')
# tree stipple clusters
cand = np.argwhere((dist_in > 25) & (fbm(H, W, 90, 3, seed=180) > 0.6))
r2.shuffle(cand)
tp = []
for (py, px) in cand[:6000]:
    if len(tp) > 260:
        break
    if any((px - qx) ** 2 + (py - qy) ** 2 < 22 ** 2 for qx, qy in tp[-60:]):
        continue
    tp.append((px, py))
    rr = r2.uniform(5, 8)
    marks += f'<circle class="t" cx="{px:.0f}" cy="{py:.0f}" r="{rr:.1f}"/><path class="tt" d="M{px} {py+rr} V{py+rr+5}"/>'

# graticule: gently curved meridians and parallels
grat = ''
for i in range(1, 8):
    xx = i * W / 8
    grat += f'<path d="M{xx} -10 Q{xx + (xx - W/2) * 0.08} {H/2} {xx} {H+10}"/>'
    yy = i * H / 8
    grat += f'<path d="M-10 {yy} Q{W/2} {yy - 26} {W+10} {yy}"/>'

# compass rose (in sea, upper right of the centre column)
ccx, ccy, R = 1190, 470, 120
def starp(cx, cy, R, r, n, rot):
    pts = []
    for i in range(n * 2):
        a = np.radians(rot + i * 180 / n)
        rr = R if i % 2 == 0 else r
        pts.append(f'{cx + rr*np.sin(a):.1f},{cy - rr*np.cos(a):.1f}')
    return ' '.join(pts)
rose_ticks = ''.join(
    f'<line x1="{ccx+R*0.92*np.sin(np.radians(a)):.1f}" y1="{ccy-R*0.92*np.cos(np.radians(a)):.1f}" x2="{ccx+R*(0.84 if a%45 else 0.78)*np.sin(np.radians(a)):.1f}" y2="{ccy-R*(0.84 if a%45 else 0.78)*np.cos(np.radians(a)):.1f}"/>'
    for a in range(0, 360, 10))
compass = f'''
<g class="ink">
<circle cx="{ccx}" cy="{ccy}" r="{R}" /><circle cx="{ccx}" cy="{ccy}" r="{R*0.92}"/>{rose_ticks}
</g>
<polygon points="{starp(ccx, ccy, R*0.78, R*0.12, 4, 45)}" fill="#b98c4c" fill-opacity=".55" stroke="#5b4026" stroke-width="1.6"/>
<polygon points="{starp(ccx, ccy, R*1.12, R*0.16, 4, 0)}" fill="#e2c38a" fill-opacity=".75" stroke="#5b4026" stroke-width="1.8"/>
<path d="M{ccx} {ccy-R*1.12} L{ccx+R*0.16*0.7} {ccy-R*0.16*0.7} L{ccx} {ccy}Z M{ccx+R*1.12} {ccy} L{ccx+R*0.11} {ccy+R*0.11} L{ccx} {ccy}Z M{ccx} {ccy+R*1.12} L{ccx-R*0.11} {ccy+R*0.11} L{ccx} {ccy}Z M{ccx-R*1.12} {ccy} L{ccx-R*0.11} {ccy-R*0.11} L{ccx} {ccy}Z" fill="#7c5a33" fill-opacity=".55"/>
<circle cx="{ccx}" cy="{ccy}" r="6" fill="#5b4026"/>
'''
# sea wave marks
waves = ''
for i in range(12):
    wx, wy = r2.integers(40, W - 40), r2.integers(40, H - 40)
    if dist_out[wy, wx] < 70:
        continue
    waves += f'<path d="M{wx} {wy} q9 -8 18 0 t18 0"/>'

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">
<style>
.ink{{fill:none;stroke:#5b4026;stroke-width:1.6;stroke-linejoin:round}}
.m{{fill:none;stroke:#6a4c2e;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}}
.ms{{fill:#7b6a54;fill-opacity:.28;stroke:none}}
.t{{fill:#6f8a5a;fill-opacity:.55;stroke:#4f5e36;stroke-width:1}}
.tt{{stroke:#4f5e36;stroke-width:1.2}}
</style>
<g fill="none" stroke="#8a6f4f" stroke-width="1" opacity=".35">{grat}</g>
<g fill="none" stroke="#4b6f78" stroke-width="1.2" opacity=".8">{ripples}</g>
<g fill="none" stroke="#3f5f68" stroke-width="1.4" opacity=".55" stroke-linecap="round">{waves}</g>
<g fill="none" stroke="#4f3820" stroke-width="2.3" stroke-linejoin="round" opacity=".85">{coast_svg}</g>
{marks}
{compass}
</svg>'''
ink = render_svg(svg, W, H, 'map_ink', transparent=True)
ia = ink[..., 3:4]
# ink bleeds slightly & breaks up on paper texture
ia = ia * (0.75 + 0.25 * smoothstep(0.2, 0.6, ph))[..., None]
col = col * (1 - ia * 0.9) + ink[..., :3] * ia * 0.9

# ---------- finish: paper edges toning, vignette ----------
edge = np.minimum.reduce([x, W - 1 - x, y, H - 1 - y])
tone = (1 - smoothstep(0, 220, edge)) * (0.5 + 0.5 * fbm(H, W, 60, 3, seed=190))
col = glaze(col, np.array([0.80, 0.66, 0.45]), tone * 0.35)
col += grain(H, W, 0.012, seed=191)
save(col, 'map.webp', q=80)
save(col, 'map-1100.webp', q=78, size=(1100, 1100))
np.save(os.path.join(TMP, 'land.npy'), landw)
print('land at meeting point (900,1050):', land[1050, 900], ' tip check', land[1150, 930], land[1250, 930])
