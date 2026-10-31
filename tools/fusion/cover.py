"""Collector's atlas front board: teal book-cloth, blind-embossed frame, gold foil title, brass corners.
Also the marbled endpaper for the inside of the board."""
from common import *

W, H = 1000, 1400
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
fr = font_b64('/home/claude/site/fusion/fonts/fraunces-latin-full-normal.woff2')
fri = font_b64('/home/claude/site/fusion/fonts/fraunces-latin-full-italic.woff2')

# ---------- cloth ----------
r = np.random.default_rng(4)
warp_threads = ndi.gaussian_filter(r.normal(0, 1, (H, W)).astype(np.float32), (40, 0.7))
weft_threads = ndi.gaussian_filter(r.normal(0, 1, (H, W)).astype(np.float32), (0.7, 40))
weave = 0.5 * np.sin(x * 2.2) * np.sin(y * 2.2)
cloth = 0.5 + 0.06 * weave + 0.05 * warp_threads / warp_threads.std() + 0.05 * weft_threads / weft_threads.std()
cloth += 0.10 * (fbm(H, W, 260, 4, seed=8) - 0.5)
base = np.array([0.085, 0.235, 0.225])
col = base[None, None, :] * (0.65 + 0.7 * cloth[..., None])
# wear at edges and corners: rubbed lighter, slightly desaturated
edge = np.minimum.reduce([x, W - 1 - x, y, H - 1 - y]) / 60
wear = (1 - smoothstep(0, 1, edge)) * (0.5 + 0.5 * fbm(H, W, 30, 3, seed=9))
col = col + wear[..., None] * np.array([0.10, 0.13, 0.12])
# hinge groove near spine (left)
hinge = np.exp(-((x - 70) / 10) ** 2) * 0.35
col *= (1 - hinge)[..., None]
col *= (0.82 + 0.18 * smoothstep(0, 70, x))[..., None]
# gentle board light from top-left
col *= (1.12 - 0.28 * (x / W * 0.4 + y / H * 0.6))[..., None]


# ---------- masks via SVG ----------
def mask(svg_body):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><defs><style>
    @font-face{{font-family:F;src:url(data:font/woff2;base64,{fr})}}
    @font-face{{font-family:FI;src:url(data:font/woff2;base64,{fri})}}</style></defs>{svg_body}</svg>'''
    return render_svg(svg, W, H, 'mask_tmp', transparent=True)[..., 3]


def star(cx, cy, R, r, n=8, rot=0):
    pts = []
    for i in range(n * 2):
        a = np.radians(rot + i * 180 / n)
        rr = R if i % 2 == 0 else r
        pts.append(f'{cx + rr*np.sin(a):.1f},{cy - rr*np.cos(a):.1f}')
    return ' '.join(pts)


blind = mask(f'''
<g fill="none" stroke="#fff">
<rect x="120" y="70" width="820" height="1260" stroke-width="5"/>
<rect x="138" y="88" width="784" height="1224" stroke-width="2"/>
<path d="M120 300 H940 M120 1100 H940" stroke-width="2"/>
</g>''')

cx, cy = 530, 760
foil = mask(f'''
<g fill="#fff" stroke="none" font-family="F">
<text x="530" y="205" text-anchor="middle" font-size="30" letter-spacing="14" style="font-variation-settings:'opsz' 9,'wght' 500">A COLLECTOR'S ATLAS</text>
<text x="530" y="420" text-anchor="middle" font-size="64" letter-spacing="22" style="font-variation-settings:'opsz' 144,'wght' 420">THE</text>
<text x="530" y="530" text-anchor="middle" font-size="128" letter-spacing="14" style="font-variation-settings:'opsz' 144,'wght' 380,'SOFT' 50">ATLAS</text>
<text x="530" y="612" text-anchor="middle" font-size="64" letter-spacing="22" style="font-variation-settings:'opsz' 144,'wght' 420">OF US</text>
</g>
<g fill="none" stroke="#fff">
<circle cx="{cx}" cy="{cy+90}" r="118" stroke-width="3"/>
<circle cx="{cx}" cy="{cy+90}" r="106" stroke-width="1.5"/>
</g>
<polygon points="{star(cx, cy+90, 96, 18, 4, 0)}" fill="#fff"/>
<polygon points="{star(cx, cy+90, 62, 12, 4, 45)}" fill="#fff"/>
<g fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round">
<path d="M{cx-320} {cy+250} C {cx-200} {cy+160} {cx-150} {cy+260} {cx} {cy+90}"/>
<path d="M{cx+320} {cy+250} C {cx+200} {cy+330} {cx+150} {cy+160} {cx} {cy+90}" stroke-dasharray="10 9"/>
</g>
<circle cx="{cx-320}" cy="{cy+250}" r="7" fill="#fff"/><circle cx="{cx+320}" cy="{cy+250}" r="7" fill="#fff"/>
<g fill="#fff" font-family="F">
<text x="530" y="1190" text-anchor="middle" font-size="40" letter-spacing="10" style="font-variation-settings:'opsz' 36,'wght' 460">AKSHAY &amp; PRIYA</text>
<text x="530" y="1250" text-anchor="middle" font-family="FI" font-size="30" style="font-variation-settings:'opsz' 36,'wght' 350">Two souls · Two journeys · One destination</text>
</g>''')

# blind emboss (debossed, darker with lit lower-right edge)
bm = ndi.gaussian_filter(blind, 1.2)
gy, gx = np.gradient(ndi.gaussian_filter(bm, 1.5))
col *= (1 - 0.35 * bm)[..., None]
col += (np.clip(gx * 2.2 + gy * 2.2, 0, 1))[..., None] * 0.25  # lit far wall
col -= (np.clip(-(gx + gy) * 2.2, 0, 1))[..., None] * 0.18

# foil: debossed then gold with micro-texture and wear breakup
fm = ndi.gaussian_filter(foil, 0.6)
gy, gx = np.gradient(ndi.gaussian_filter(fm, 1.4))
shadow = np.clip(-(gx + gy) * 3, 0, 1)
col -= shadow[..., None] * 0.25
gold_n = fbm(H, W, 40, 4, seed=21)
spec = np.exp(-(((x * 0.6 + y * 0.8) - 700) / 260) ** 2)  # broad sheen band
g1 = np.array([0.53, 0.38, 0.16]); g2 = np.array([0.95, 0.82, 0.52]); g3 = np.array([1.0, 0.95, 0.80])
gold = g1 + (g2 - g1) * (0.35 + 0.5 * gold_n)[..., None]
gold = gold + (g3 - gold) * (spec * 0.75)[..., None]
breakup = smoothstep(0.18, 0.30, fbm(H, W, 6, 3, seed=33) * 0.5 + 0.5 * (1 - wear))
fa = (fm * (0.82 + 0.18 * breakup))[..., None]
col = col * (1 - fa) + gold * fa

# ---------- brass corners (right side only + spine side covered by cloth spine) ----------
corn = render_svg(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><defs>
<linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6dc9a"/><stop offset=".3" stop-color="#c79a48"/><stop offset=".65" stop-color="#8b6224"/><stop offset="1" stop-color="#d9b46a"/></linearGradient>
<filter id="s"><feDropShadow dx="3" dy="4" stdDeviation="3" flood-color="#000" flood-opacity=".55"/></filter></defs>
<g filter="url(#s)" fill="url(#b)" stroke="#5b3d12" stroke-width="1.5">
<path d="M{W} 0 H{W-150} Q{W-120} 8 {W-112} 26 L{W-26} 112 Q{W-8} 120 {W} 150Z"/>
<path d="M{W} {H} H{W-150} Q{W-120} {H-8} {W-112} {H-26} L{W-26} {H-112} Q{W-8} {H-120} {W} {H-150}Z"/>
<path d="M0 0 H150 Q120 8 112 26 L26 112 Q8 120 0 150Z"/>
<path d="M0 {H} H150 Q120 {H-8} 112 {H-26} L26 {H-112} Q8 {H-120} 0 {H-150}Z"/>
</g>
<g fill="#7a5420">
<circle cx="{W-40}" cy="40" r="5"/><circle cx="{W-40}" cy="{H-40}" r="5"/><circle cx="40" cy="40" r="5"/><circle cx="40" cy="{H-40}" r="5"/></g>
<g fill="#fbe7b0" opacity=".8">
<circle cx="{W-42}" cy="38" r="2"/><circle cx="{W-42}" cy="{H-42}" r="2"/><circle cx="38" cy="38" r="2"/><circle cx="38" cy="{H-42}" r="2"/></g>
</svg>''', W, H, 'corners', transparent=True)
ca = corn[..., 3:4]
cn = fbm(H, W, 12, 3, seed=44)[..., None]
col = col * (1 - ca) + corn[..., :3] * (0.88 + 0.24 * cn) * ca

col = col + grain(H, W, 0.018, seed=12)
alpha = np.ones((H, W, 1), np.float32)
# rounded board corners (very slight)
save(np.concatenate([col, alpha], -1), 'cover.webp', q=82)
save(np.concatenate([col, alpha], -1), 'cover-640.webp', q=80, size=(640, 896))

# ---------- marbled endpaper ----------
EW, EH = 700, 980
ey, ex = np.mgrid[0:EH, 0:EW].astype(np.float32)
wx = (fbm(EH, EW, 220, 4, seed=51) - .5) * 260
wy = (fbm(EH, EW, 180, 4, seed=52) - .5) * 200
u = ex + wx + 40 * np.sin(ey / 37)
v = ey + wy
comb = np.sin(u / 9.0 + 3 * np.sin(v / 60))
bands = np.sin(v / 23.0 + wx / 30)
t = 0.5 + 0.35 * comb * 0.6 + 0.4 * bands * 0.5
teal = np.array([0.09, 0.27, 0.26]); cream = np.array([0.93, 0.88, 0.76]); goldc = np.array([0.78, 0.62, 0.33]); rose = np.array([0.72, 0.45, 0.43])
ecol = teal + (cream - teal) * smoothstep(0.45, 0.75, t)[..., None]
veins = smoothstep(0.92, 0.99, np.abs(np.sin(u / 14 + v / 90)))
ecol = ecol * (1 - veins[..., None] * 0.6) + goldc * veins[..., None] * 0.6
spots = smoothstep(0.62, 0.68, fbm(EH, EW, 26, 2, seed=55))
ecol = ecol * (1 - spots[..., None] * 0.5) + rose * spots[..., None] * 0.5
ecol *= (0.9 + 0.1 * fbm(EH, EW, 4, 2, seed=56))[..., None]
# inner hinge shadow on the right edge (spine side when opened)
ecol *= (1 - 0.45 * np.exp(-((EW - ex) / 40) ** 2))[..., None]
ecol += grain(EH, EW, 0.015, seed=57)
save(ecol, 'endpaper.webp', q=78)
