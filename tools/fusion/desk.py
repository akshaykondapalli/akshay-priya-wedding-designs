"""Top-down walnut desk with brass compass + jasmine sprig, lit by warm window light."""
from common import *

S = 1800
H = W = S
y, x = np.mgrid[0:H, 0:W].astype(np.float32)

# --- walnut planks (grain runs vertically) ---
plank_w = 470
pid = ((x + 130) // plank_w).astype(int)
wood = np.zeros((H, W), np.float32)
for k in range(-1, 6):
    m = pid == k
    r = np.random.default_rng(100 + k)
    streak = np.zeros((H, W), np.float32)
    for sx_, sy_, a in [(1.2, 90, .5), (3, 160, .35), (8, 300, .25)]:
        n = r.normal(0, 1, (H, W)).astype(np.float32)
        n = ndi.gaussian_filter(n, (sy_, sx_))
        streak += a * n / (n.std() + 1e-6)
    slow = (fbm(H, W, 700, 3, seed=7 + k) - .5) * 260
    rings = np.sin((x + slow + 0.00018 * (y - H * (0.3 + 0.1 * k)) ** 2) * 0.05)
    rings = np.sign(rings) * np.abs(rings) ** 0.6
    v = 0.5 + 0.10 * rings + 0.11 * streak + 0.08 * (fbm(H, W, 500, 2, seed=60 + k) - .5)
    wood[m] = v[m] + 0.04 * (k % 2)
# seams
sx = ((x + 130) % plank_w)
seam = np.exp(-((sx - 0) ** 2) / 3) + np.exp(-((sx - plank_w) ** 2) / 3)
wood -= seam * 0.35
wood = np.clip(wood, 0, 1)

c_dark = np.array([0.105, 0.062, 0.040])
c_mid = np.array([0.29, 0.175, 0.105])
c_light = np.array([0.46, 0.30, 0.18])
t = wood[..., None]
col = np.where(t < 0.5, c_dark + (c_mid - c_dark) * (t / 0.5), c_mid + (c_light - c_mid) * ((t - 0.5) / 0.5))

# lighting: warm window light from upper-left, falloff
d = np.sqrt(((x - W * 0.18) / W) ** 2 + ((y - H * 0.05) / H) ** 2)
light = 1.15 * np.exp(-d * 1.4) + 0.16
d2 = np.sqrt(((x - W * 0.5) / W) ** 2 + ((y - H * 0.47) / H) ** 2)
light = light + 0.55 * np.exp(-(d2 / 0.28) ** 2)
col = col * light[..., None] * np.array([1.08, 0.98, 0.86])
# soft window-bar shadows (very subtle)
bars = 1 - 0.10 * smoothstep(0.0, 0.08, np.abs(((x * 0.72 + y * 0.69) % 900) - 450) / 900 - 0.40)
col *= bars[..., None]
# varnish sheen
sheen = np.exp(-(((x - W * 0.3) / (W * 0.25)) ** 2 + ((y - H * 0.18) / (H * 0.18)) ** 2)) * 0.10
col = col + sheen[..., None] * np.array([1, .85, .6])

# --- props (SVG) ---
fr = font_b64('/home/claude/site/fusion/fonts/fraunces-latin-full-normal.woff2')


def jasmine(cx, cy, r, rot, op=1):
    petals = ''
    for i in range(5):
        a = rot + i * 72
        petals += f'<ellipse cx="0" cy="{-r*0.62}" rx="{r*0.36}" ry="{r*0.62}" transform="rotate({a})" fill="url(#pet)" stroke="#d9cdb8" stroke-width="0.6"/>'
    return f'<g transform="translate({cx},{cy})" opacity="{op}" filter="url(#fs)">{petals}<circle r="{r*0.13}" fill="#e9d48f"/><circle r="{r*0.07}" fill="#c7a24a"/></g>'


def bud(cx, cy, l, rot):
    return f'<g transform="translate({cx},{cy}) rotate({rot})" filter="url(#fs)"><path d="M0 0 C {l*0.18} {-l*0.3} {l*0.16} {-l*0.8} 0 {-l} C {-l*0.16} {-l*0.8} {-l*0.18} {-l*0.3} 0 0Z" fill="url(#bud)"/><path d="M0 0 L0 {l*0.5}" stroke="#56703f" stroke-width="2.2"/></g>'


def leaf(cx, cy, l, rot):
    return f'<g transform="translate({cx},{cy}) rotate({rot})" filter="url(#fs)"><path d="M0 0 C {l*0.32} {-l*0.25} {l*0.3} {-l*0.75} 0 {-l} C {-l*0.3} {-l*0.75} {-l*0.32} {-l*0.25} 0 0Z" fill="url(#lf)"/><path d="M0 0 L0 {-l*0.95}" stroke="#a7b98a" stroke-width="1.2" opacity=".55"/></g>'


svg_parts = []
# jasmine sprig upper-right
stem = '<path d="M1810 210 C 1650 260 1540 300 1420 420 C 1360 480 1330 520 1300 600" stroke="#4d6436" stroke-width="5" fill="none" filter="url(#fs)"/>'
svg_parts.append(stem)
for (lx, ly, ll, lr) in [(1700, 240, 120, -70), (1600, 285, 110, 100), (1500, 330, 115, -40), (1440, 400, 100, 140), (1360, 500, 95, -30), (1330, 560, 90, 120)]:
    svg_parts.append(leaf(lx, ly, ll, lr))
for (jx, jy, jr, ro) in [(1560, 300, 46, 10), (1420, 445, 52, 40), (1320, 610, 44, 0), (1655, 200, 40, 25), (1475, 360, 38, 60)]:
    svg_parts.append(jasmine(jx, jy, jr, ro))
for (bx, by, bl, br) in [(1520, 250, 54, 20), (1380, 520, 50, -25), (1290, 650, 46, 10), (1600, 360, 48, 150)]:
    svg_parts.append(bud(bx, by, bl, br))
# loose petals / flowers near bottom-left
for (jx, jy, jr, ro, op) in [(240, 1480, 40, 15, 1), (330, 1560, 34, 50, .95), (180, 1610, 30, 0, .9)]:
    svg_parts.append(jasmine(jx, jy, jr, ro, op))
for (px, py, pr) in [(420, 1440, 20), (130, 1380, 30), (470, 1650, -40)]:
    svg_parts.append(f'<ellipse cx="{px}" cy="{py}" rx="12" ry="22" transform="rotate({pr} {px} {py})" fill="url(#pet)" filter="url(#fs)"/>')

# brass compass lower-right
cx, cy, R = 1490, 1480, 175
ticks = ''
for i in range(72):
    a = np.radians(i * 5)
    r1 = R * 0.78
    r2 = R * (0.70 if i % 2 == 0 else 0.74)
    if i % 18 == 0:
        r2 = R * 0.64
    ticks += f'<line x1="{cx+r1*np.sin(a):.1f}" y1="{cy-r1*np.cos(a):.1f}" x2="{cx+r2*np.sin(a):.1f}" y2="{cy-r2*np.cos(a):.1f}" stroke="#4a3412" stroke-width="{2 if i%18==0 else 1}"/>'
star = ''
for i, (ln, w, c1) in enumerate([(0.6, 0.11, '#7a1f2b'), (0.6, 0.11, '#2b2a24'), (0.42, 0.08, '#2b2a24'), (0.42, 0.08, '#2b2a24')]):
    pass
needle = f'<g transform="translate({cx},{cy}) rotate(-28)"><path d="M0 {-R*0.6} L{R*0.07} 0 L0 {R*0.6} L{-R*0.07} 0Z" fill="#2c2620"/><path d="M0 {-R*0.6} L{R*0.07} 0 L{-R*0.07} 0Z" fill="#8c2232"/><circle r="{R*0.06}" fill="url(#brass)" stroke="#5a3d12"/></g>'
compass = f'''
<g filter="url(#ds)">
  <circle cx="{cx+R*0.95}" cy="{cy-R*0.95}" r="{R*0.17}" fill="none" stroke="url(#brass)" stroke-width="14"/>
  <circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#brass)"/>
</g>
<circle cx="{cx}" cy="{cy}" r="{R*0.93}" fill="none" stroke="#6b4a17" stroke-width="3"/>
<circle cx="{cx}" cy="{cy}" r="{R*0.86}" fill="url(#dial)"/>
{ticks}
<text x="{cx}" y="{cy-R*0.47}" text-anchor="middle" font-family="F" font-size="30" fill="#3d2a10">N</text>
<text x="{cx}" y="{cy+R*0.57}" text-anchor="middle" font-family="F" font-size="26" fill="#3d2a10">S</text>
<text x="{cx+R*0.52}" y="{cy+9}" text-anchor="middle" font-family="F" font-size="26" fill="#3d2a10">E</text>
<text x="{cx-R*0.52}" y="{cy+9}" text-anchor="middle" font-family="F" font-size="26" fill="#3d2a10">W</text>
{needle}
<circle cx="{cx}" cy="{cy}" r="{R*0.86}" fill="url(#glass)"/>
'''
svg_parts.append(compass)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
<defs>
<style>@font-face{{font-family:F;src:url(data:font/woff2;base64,{fr})}}</style>
<radialGradient id="pet" cx="35%" cy="30%" r="80%"><stop offset="0" stop-color="#fffdf7"/><stop offset=".7" stop-color="#f3ecdf"/><stop offset="1" stop-color="#d8cbb2"/></radialGradient>
<linearGradient id="bud" x1="0" x2="1"><stop offset="0" stop-color="#f6efe0"/><stop offset=".6" stop-color="#e9dcc4"/><stop offset="1" stop-color="#c9a9a0"/></linearGradient>
<linearGradient id="lf" x1="0" x2="1"><stop offset="0" stop-color="#3f5a2c"/><stop offset=".5" stop-color="#5f7c40"/><stop offset="1" stop-color="#2f4521"/></linearGradient>
<radialGradient id="brass" cx="35%" cy="30%" r="85%"><stop offset="0" stop-color="#f7dc95"/><stop offset=".35" stop-color="#c99a45"/><stop offset=".75" stop-color="#8a6022"/><stop offset="1" stop-color="#5b3c12"/></radialGradient>
<radialGradient id="dial" cx="45%" cy="40%" r="70%"><stop offset="0" stop-color="#f3e6c6"/><stop offset="1" stop-color="#d8c296"/></radialGradient>
<radialGradient id="glass" cx="32%" cy="25%" r="75%"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".25" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity=".12"/></radialGradient>
<filter id="fs" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="9" dy="12" stdDeviation="7" flood-color="#120802" flood-opacity=".55"/></filter>
<filter id="ds" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="22" dy="26" stdDeviation="16" flood-color="#0c0502" flood-opacity=".7"/></filter>
</defs>
{''.join(svg_parts)}
</svg>'''
props = render_svg(svg, S, S, 'desk_props', transparent=True)
pa = props[..., 3:4]
# props get the same warm light
props_rgb = props[..., :3] * (0.55 + 0.6 * light[..., None] / light.max())
col = col * (1 - pa) + props_rgb * pa

# vignette + grain
v = 1 - 0.55 * smoothstep(0.35, 1.0, np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / 1.2)
col = col * v[..., None]
col = col + grain(H, W, 0.022)
np.save(os.path.join(TMP, 'desk_light.npy'), light.astype(np.float32))
save(col, 'desk.webp', q=74)
save(col, 'desk-1000.webp', q=72, size=(1000, 1000))
