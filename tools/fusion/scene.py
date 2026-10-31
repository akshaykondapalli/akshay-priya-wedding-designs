"""Godavari-dusk mandapam courtyard, built in true 3D perspective and rendered twice:
   scene-real.webp  (luminous, lamp-lit, hazy, depth-of-field)
   scene-water.webp (hand-painted watercolor of the identical composition)
Also writes lamps.json (normalised lamp positions) for the in-browser ignition."""
from common import *
import json, math

S = 1800
W = H = S
HZ = 820          # horizon line
F = 1100          # focal length px
CH = 1.6          # camera height (m)
CX = 900
y, x = np.mgrid[0:H, 0:W].astype(np.float32)


def P(u, h, z):
    return CX + F * u / z, HZ + F * (CH - h) / z


def pts(lst):
    return ' '.join(f'{a:.1f},{b:.1f}' for a, b in lst)


def poly(lst, **kw):
    attrs = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<polygon points="{pts(lst)}" {attrs}/>'


def quad(u0, u1, h0, h1, z, **kw):
    return poly([P(u0, h0, z), P(u1, h0, z), P(u1, h1, z), P(u0, h1, z)], **kw)


rng2 = np.random.default_rng(77)
DEFS = '''
<linearGradient id="stone" x1="0" x2="1"><stop offset="0" stop-color="#cdb08a"/><stop offset=".45" stop-color="#ead2a8"/><stop offset="1" stop-color="#9c7f5c"/></linearGradient>
<linearGradient id="pillar" x1="0" x2="1"><stop offset="0" stop-color="#6e5a43"/><stop offset=".35" stop-color="#e7cfa4"/><stop offset=".6" stop-color="#c9ab80"/><stop offset="1" stop-color="#5d4a36"/></linearGradient>
<linearGradient id="gold" x1="0" x2="1"><stop offset="0" stop-color="#7a5418"/><stop offset=".4" stop-color="#f3d58b"/><stop offset=".7" stop-color="#b98b37"/><stop offset="1" stop-color="#6a4610"/></linearGradient>
<linearGradient id="goldv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6dc96"/><stop offset=".5" stop-color="#c0913f"/><stop offset="1" stop-color="#6d4812"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9d2a4"/><stop offset=".5" stop-color="#c7a473"/><stop offset="1" stop-color="#7d6243"/></linearGradient>
<linearGradient id="roof" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d9b98a"/><stop offset="1" stop-color="#8c6e4c"/></linearGradient>
<linearGradient id="drape" spreadMethod="reflect" gradientUnits="userSpaceOnUse" x1="0" x2="34"><stop offset="0" stop-color="#b9485a"/><stop offset=".5" stop-color="#e88a7e"/><stop offset="1" stop-color="#9e3448"/></linearGradient>
<linearGradient id="drapeG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".35"/><stop offset=".3" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".15"/></linearGradient>
<radialGradient id="pot" cx="35%" cy="35%" r="75%"><stop offset="0" stop-color="#fbe3a0"/><stop offset=".4" stop-color="#c9963f"/><stop offset="1" stop-color="#5e3d0e"/></radialGradient>
<radialGradient id="coco" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#b98a55"/><stop offset="1" stop-color="#5b3b1d"/></radialGradient>
<radialGradient id="jas" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#fffef8"/><stop offset="1" stop-color="#d9d0bc"/></radialGradient>
<radialGradient id="mari" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#ffc24a"/><stop offset=".7" stop-color="#f08a12"/><stop offset="1" stop-color="#b85a06"/></radialGradient>
<radialGradient id="mariR" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#ff9a6a"/><stop offset=".7" stop-color="#d84a22"/><stop offset="1" stop-color="#8f2410"/></radialGradient>
<linearGradient id="leaf" x1="0" x2="1"><stop offset="0" stop-color="#2f5a24"/><stop offset=".5" stop-color="#5c8e38"/><stop offset="1" stop-color="#28481c"/></linearGradient>
<linearGradient id="banana" x1="0" x2="1"><stop offset="0" stop-color="#3e6e2a"/><stop offset=".5" stop-color="#86b052"/><stop offset="1" stop-color="#355e22"/></linearGradient>
<linearGradient id="bstem" x1="0" x2="1"><stop offset="0" stop-color="#5d7d39"/><stop offset=".5" stop-color="#a7c171"/><stop offset="1" stop-color="#4a6a2a"/></linearGradient>
'''


def svgdoc(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{DEFS}</defs>{body}</svg>'


# ======================= LAYER: far (palms, treeline, compound wall) =======================
def palm(bx, by, hgt, lean, fronds=11, scale=1.0, color='#123238'):
    tx, ty = bx + lean, by - hgt
    out = f'<path d="M{bx-6*scale} {by} Q{bx+lean*0.3} {by-hgt*0.5} {tx-2*scale} {ty} L{tx+3*scale} {ty} Q{bx+lean*0.3+8*scale} {by-hgt*0.5} {bx+6*scale} {by}Z" fill="{color}"/>'
    for i in range(fronds):
        a = math.radians(-180 + i * (360 / fronds) + rng2.uniform(-12, 12))
        L = rng2.uniform(70, 110) * scale
        droop = rng2.uniform(0.35, 0.8)
        ex, ey = tx + math.cos(a) * L, ty + math.sin(a) * L * 0.55 + L * droop
        mx, my = tx + math.cos(a) * L * 0.55, ty + math.sin(a) * L * 0.4 - L * 0.12
        out += f'<path d="M{tx} {ty} Q{mx} {my} {ex} {ey}" stroke="{color}" stroke-width="{3*scale}" fill="none"/>'
        # leaflets
        for t in np.linspace(0.15, 0.95, 9):
            px = (1 - t) ** 2 * tx + 2 * (1 - t) * t * mx + t * t * ex
            py = (1 - t) ** 2 * ty + 2 * (1 - t) * t * my + t * t * ey
            ll = (1 - t * 0.6) * 26 * scale
            out += f'<path d="M{px:.1f} {py:.1f} l{-ll*0.5:.1f} {ll:.1f} M{px:.1f} {py:.1f} l{ll*0.5:.1f} {ll*0.9:.1f}" stroke="{color}" stroke-width="{1.6*scale}"/>'
    return out


far = ''
# distant treeline band
tl = 'M0 860 ' + ' '.join(f'L{xx} {845 - 18 * math.sin(xx / 47) - 12 * math.sin(xx / 13 + 1) - rng2.uniform(0, 10):.0f}' for xx in range(0, W + 30, 30)) + f' L{W} 900 L0 900Z'
far += f'<path d="{tl}" fill="#2a4a4c" opacity=".55"/>'
# far palms (hazy)
for xx in list(range(-40, 560, 70)) + list(range(1260, W + 60, 70)):
    far += palm(xx + rng2.uniform(-20, 20), 860, rng2.uniform(170, 260), rng2.uniform(-40, 40), scale=0.75, color='#2b4c50')
# compound wall at z=11
wall = quad(-9, 9, 0, 1.15, 11, fill='#b99a74')
coping = quad(-9, 9, 1.15, 1.28, 11, fill='#e2c9a0')
far += wall + coping
# niches with tiny lamp alcoves in the wall
for u in np.arange(-8.4, 8.6, 1.2):
    if abs(u) < 2.2:
        continue
    a0 = P(u - 0.2, 0.35, 11); a1 = P(u + 0.2, 0.85, 11)
    far += f'<path d="M{a0[0]:.1f} {a0[1]:.1f} V{a1[1]+6:.1f} Q{(a0[0]+a1[0])/2:.1f} {a1[1]-6:.1f} {a1[0]:.1f} {a1[1]+6:.1f} V{a0[1]:.1f}Z" fill="#6b5039"/>'
# nearer palms behind wall
for (u, z, hh, ln) in [(-7.5, 16, 7.5, -30), (-5.2, 19, 8.5, 20), (-3.6, 24, 9, -10), (4.0, 22, 8.8, 15), (5.6, 17, 8, -25), (7.8, 15, 7, 30), (-9.5, 14, 7, 10), (9.8, 14, 7.2, -15)]:
    bx, by = P(u, 0, z)
    sc = 11 / z * 1.25
    far += palm(bx, by, F * hh / z, ln * sc, fronds=12, scale=sc, color='#183c40')

# ======================= LAYER: ground =======================
gnd = ''
# stone path slabs between lamp rows
for zi in np.arange(1.8, 4.3, 0.4):
    for ui in np.arange(-1.0, 1.01, 0.5):
        pass
# muggu (kolam) projected on the ground: dots + curved loops (sikku style lattice), centred u=0, z 2.0-3.9
mug_lines = []
cell = 0.14
NU, NZ = 7, 7
cu, cz = 0.0, 3.2
def G(u, z):
    return P(u, 0.002, z)
dots = []
for i in range(-NU // 2 + 1, NU // 2 + 1):
    for j in range(-NZ // 2 + 1, NZ // 2 + 1):
        if abs(i) + abs(j) <= 3:
            dots.append((cu + i * cell * 1.0, cz + j * cell * 1.15))
# loops around each dot (diamond with curled corners)
for (u, z) in dots:
    r = cell * 0.48
    loop = []
    for t in np.linspace(0, 2 * np.pi, 40):
        rr = r * (0.75 + 0.25 * np.cos(4 * t))
        loop.append(G(u + rr * np.cos(t), z + rr * np.sin(t) * 1.15))
    mug_lines.append(loop)
# outer petals ring
for k in range(16):
    a = 2 * np.pi * k / 16
    petal = []
    for t in np.linspace(-0.5, 0.5, 20):
        rr = 0.589 + 0.155 * np.cos(t * np.pi)
        aa = a + t * 0.35
        petal.append(G(cu + rr * np.cos(aa), cz + rr * np.sin(aa) * 1.1))
    mug_lines.append(petal)
ring = [G(cu + 0.533 * np.cos(t), cz + 0.533 * np.sin(t) * 1.1) for t in np.linspace(0, 2 * np.pi, 120)]
ring2 = [G(cu + 0.794 * np.cos(t), cz + 0.794 * np.sin(t) * 1.1) for t in np.linspace(0, 2 * np.pi, 160)]
mug_lines += [ring, ring2]
mugg = ''.join(f'<polyline points="{pts(l)}" fill="none" stroke="#fbf6ea" stroke-width="{2.2}" stroke-linecap="round" stroke-linejoin="round"/>' for l in mug_lines)
mugg += ''.join(f'<circle cx="{G(u, z)[0]:.1f}" cy="{G(u, z)[1]:.1f}" r="3.4" fill="#fbf6ea"/>' for (u, z) in dots)
# turmeric/kumkum fill accents inside outer ring
for k in range(16):
    a = 2 * np.pi * (k + 0.5) / 16
    p = G(cu + 0.670 * np.cos(a), cz + 0.670 * np.sin(a) * 1.1)
    gnd += f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{4 + 3*(p[1]-1100)/600:.1f}" fill="{"#e2a21c" if k%2 else "#b3262f"}"/>'
gnd += mugg
# marigold petal border lines along the path edges
for side in (-1, 1):
    for z in np.arange(2.25, 4.15, 0.03):
        u = side * (0.72 + rng2.uniform(-0.02, 0.02))
        p = G(u, z)
        rr = 26 / z
        gnd += f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{rr:.1f}" fill="url(#{"mari" if rng2.random()>0.3 else "mariR"})"/>'

# ======================= LAYER: mandapam =======================
md = ''
ZF, ZB, UP = 4.9, 6.9, 1.55
PH0, PH1 = 0.45, 3.3
# back drape (rose silk with folds)
dl = P(-1.5, PH0, ZB + 0.08); dr = P(1.5, PH1, ZB + 0.08)
md += f'<rect x="{dl[0]:.1f}" y="{dr[1]:.1f}" width="{dr[0]-dl[0]:.1f}" height="{dl[1]-dr[1]:.1f}" fill="url(#drape)"/>'
md += f'<rect x="{dl[0]:.1f}" y="{dr[1]:.1f}" width="{dr[0]-dl[0]:.1f}" height="{dl[1]-dr[1]:.1f}" fill="url(#drapeG)"/>'
# gold-bordered swag across the top of the drape
sw = ''
for k in range(5):
    u0 = -1.5 + k * 0.6; u1 = u0 + 0.6
    a = P(u0, PH1 - 0.05, ZB + 0.05); b = P(u1, PH1 - 0.05, ZB + 0.05); m = P((u0 + u1) / 2, PH1 - 0.45, ZB + 0.05)
    sw += f'<path d="M{a[0]:.1f} {a[1]:.1f} Q{m[0]:.1f} {m[1]+22:.1f} {b[0]:.1f} {b[1]:.1f}" stroke="url(#gold)" stroke-width="7" fill="none"/>'
md += sw
# dais
md += poly([P(-1.95, PH0, 4.55), P(1.95, PH0, 4.55), P(1.95, PH0, 7.2), P(-1.95, PH0, 7.2)], fill='#e9d7b6')
md += quad(-1.95, 1.95, 0, PH0, 4.55, fill='url(#stone)')
# gold band on dais front
md += quad(-1.95, 1.95, PH0 - 0.08, PH0 - 0.03, 4.55, fill='url(#gold)')
# steps
md += quad(-0.9, 0.9, 0, 0.15, 4.15, fill='#d8bf98') + poly([P(-0.9, 0.15, 4.15), P(0.9, 0.15, 4.15), P(0.9, 0.15, 4.35), P(-0.9, 0.15, 4.35)], fill='#f1e2c6')
md += quad(-0.9, 0.9, 0.15, 0.30, 4.35, fill='#d0b48a') + poly([P(-0.9, 0.30, 4.35), P(0.9, 0.30, 4.35), P(0.9, 0.30, 4.55), P(-0.9, 0.30, 4.55)], fill='#efdfc2')


def pillar(u, z, w=0.22):
    o = ''
    o += quad(u - w / 2, u + w / 2, PH0, PH1, z, fill='url(#pillar)')
    # base & capital mouldings in gold
    for (h0, h1, ww) in [(PH0, PH0 + 0.18, w * 1.5), (PH0 + 0.18, PH0 + 0.24, w * 1.3), (PH1 - 0.3, PH1 - 0.22, w * 1.25), (PH1 - 0.22, PH1, w * 1.55)]:
        o += quad(u - ww / 2, u + ww / 2, h0, h1, z, fill='url(#gold)')
    # carved bands
    for hb in np.arange(PH0 + 0.6, PH1 - 0.4, 0.55):
        o += quad(u - w * 0.56, u + w * 0.56, hb, hb + 0.05, z, fill='url(#gold)')
    return o


# back pillars first
md += pillar(-UP, ZB) + pillar(UP, ZB)
# kalasam on the dais (brass pot, mango leaves, coconut)
kc = P(0, PH0, 6.0)
ks = F / 6.0
pot_r = 0.17 * ks
pot_cy = kc[1] - pot_r * 1.05
md += f'<ellipse cx="{kc[0]:.1f}" cy="{kc[1]-2:.1f}" rx="{pot_r*1.2:.1f}" ry="{pot_r*0.22:.1f}" fill="#7a5a2a" opacity=".6"/>'
md += f'<ellipse cx="{kc[0]:.1f}" cy="{pot_cy:.1f}" rx="{pot_r:.1f}" ry="{pot_r*1.0:.1f}" fill="url(#pot)"/>'
md += f'<rect x="{kc[0]-pot_r*0.45:.1f}" y="{pot_cy-pot_r*1.35:.1f}" width="{pot_r*0.9:.1f}" height="{pot_r*0.5:.1f}" fill="url(#gold)"/>'
for k in range(7):
    a = math.radians(-150 + k * 20)
    lx = kc[0] + math.cos(a) * pot_r * 0.9
    ly = pot_cy - pot_r * 1.3 + math.sin(a) * pot_r * 0.4
    md += f'<path d="M{kc[0]:.1f} {pot_cy-pot_r*1.3:.1f} Q{lx:.1f} {ly-pot_r*0.3:.1f} {lx+math.cos(a)*pot_r*0.5:.1f} {ly+pot_r*0.6:.1f} Q{lx:.1f} {ly+pot_r*0.1:.1f} {kc[0]:.1f} {pot_cy-pot_r*1.3:.1f}Z" fill="url(#leaf)"/>'
md += f'<ellipse cx="{kc[0]:.1f}" cy="{pot_cy-pot_r*1.62:.1f}" rx="{pot_r*0.5:.1f}" ry="{pot_r*0.58:.1f}" fill="url(#coco)"/>'
md += f'<path d="M{kc[0]-pot_r*0.95:.1f} {pot_cy-pot_r*0.1:.1f} Q{kc[0]:.1f} {pot_cy+pot_r*0.25:.1f} {kc[0]+pot_r*0.95:.1f} {pot_cy-pot_r*0.1:.1f}" stroke="#b3262f" stroke-width="4" fill="none"/>'
# side beams (visible underside) & front beam
for side in (-1, 1):
    md += poly([P(side * 1.7, PH1, ZF), P(side * 1.7, PH1, ZB), P(side * 1.7, PH1 + 0.4, ZB), P(side * 1.7, PH1 + 0.4, ZF)], fill='#a88a62')
md += poly([P(-1.7, PH1, ZF), P(1.7, PH1, ZF), P(1.7, PH1, ZB), P(-1.7, PH1, ZB)], fill='#5e4733')  # ceiling
# ceiling coffers
for ui in np.arange(-1.5, 1.6, 0.5):
    md += f'<line x1="{P(ui, PH1, ZF)[0]:.1f}" y1="{P(ui, PH1, ZF)[1]:.1f}" x2="{P(ui, PH1, ZB)[0]:.1f}" y2="{P(ui, PH1, ZB)[1]:.1f}" stroke="#c49a52" stroke-width="2"/>'
md += pillar(-UP, ZF) + pillar(UP, ZF)
md += quad(-1.78, 1.78, PH1, PH1 + 0.42, ZF, fill='url(#beam)')
md += quad(-1.78, 1.78, PH1 + 0.04, PH1 + 0.08, ZF, fill='url(#gold)')
md += quad(-1.78, 1.78, PH1 + 0.34, PH1 + 0.38, ZF, fill='url(#gold)')
# carved lotus medallions on the beam
for ui in np.arange(-1.4, 1.5, 0.35):
    c = P(ui, PH1 + 0.21, ZF)
    md += f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.075*F/ZF:.1f}" fill="url(#pot)" stroke="#6b4a1a" stroke-width="1.2"/>'
# roof tiers (front faces sloping back)
tiers = [(1.9, 3.72, 1.62, 4.15), (1.55, 4.15, 1.2, 4.55), (1.15, 4.55, 0.75, 4.95)]
for k, (ub, hb, ut, ht) in enumerate(tiers):
    zb = ZF - 0.12 + k * 0.32
    zt = zb + 0.32
    md += poly([P(-ub, hb, zb), P(ub, hb, zb), P(ut, ht, zt), P(-ut, ht, zt)], fill='url(#roof)')
    md += quad(-ub, ub, hb, hb + 0.06, zb, fill='url(#gold)')
    # tile ridges
    for t in np.linspace(-1, 1, 13):
        a = P(t * ub, hb, zb); b = P(t * ut, ht, zt)
        md += f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#7a5d3e" stroke-width="1.4" opacity=".6"/>'
# finials (kalasams) on the crown
for uu in (-0.5, 0, 0.5):
    c = P(uu, 4.95, ZF + 0.84)
    s = F / (ZF + 0.84) * (0.16 if uu == 0 else 0.11)
    md += f'<ellipse cx="{c[0]:.1f}" cy="{c[1]-s*0.7:.1f}" rx="{s*0.6:.1f}" ry="{s*0.55:.1f}" fill="url(#pot)"/>'
    md += f'<ellipse cx="{c[0]:.1f}" cy="{c[1]-s*1.45:.1f}" rx="{s*0.4:.1f}" ry="{s*0.32:.1f}" fill="url(#pot)"/>'
    md += f'<path d="M{c[0]-s*0.12:.1f} {c[1]-s*1.7:.1f} L{c[0]:.1f} {c[1]-s*2.5:.1f} L{c[0]+s*0.12:.1f} {c[1]-s*1.7:.1f}Z" fill="url(#gold)"/>'

# ======================= LAYER: decor (jasmine strands, marigold swags, thoranam) =======================
dec = ''
# jasmine curtains between outer pillars and centre, hanging from beam underside
for ui in np.arange(-1.62, 1.63, 0.075):
    if abs(ui) < 0.62:
        length = 0.35 + 0.25 * (abs(ui) / 0.62)  # shorter in the centre opening
    else:
        length = 0.95 - 0.25 * ((abs(ui) - 0.62) / 1.0)
    top = P(ui, PH1, ZF - 0.02)
    bot = P(ui, PH1 - length, ZF - 0.02)
    n = int((bot[1] - top[1]) / 9)
    for k in range(n):
        yy = top[1] + k * 9 + 4
        xx = top[0] + math.sin(k * 0.6 + ui * 9) * 1.2
        c = 'url(#jas)' if (k % 9) != 8 else 'url(#mari)'
        dec += f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="{4.3 if c=="url(#jas)" else 5:.1f}" fill="{c}"/>'
    # tassel
    dec += f'<circle cx="{bot[0]:.1f}" cy="{bot[1]+4:.1f}" r="6" fill="url(#mariR)"/>'
# marigold swags (thick garlands) across the front beam
for (u0, u1, sag) in [(-1.78, -0.6, 0.38), (-0.6, 0.6, 0.30), (0.6, 1.78, 0.38)]:
    a = P(u0, PH1 + 0.02, ZF - 0.05); b = P(u1, PH1 + 0.02, ZF - 0.05)
    m = P((u0 + u1) / 2, PH1 + 0.02 - sag, ZF - 0.05)
    for t in np.linspace(0, 1, 70):
        px = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * m[0] + t * t * b[0]
        py = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * (m[1] + 40) + t * t * b[1]
        dec += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="12" fill="url(#{"mari" if int(t*70)%5 else "mariR"})"/>'
# mango-leaf thoranam along the top of the beam
for ui in np.arange(-1.74, 1.75, 0.085):
    c = P(ui, PH1 + 0.42, ZF - 0.06)
    L = 0.24 * F / ZF
    rot = math.sin(ui * 7) * 6
    dec += (f'<g transform="translate({c[0]:.1f},{c[1]:.1f}) rotate({rot:.1f})"><path d="M0 0 C {L*0.22} {L*0.2} {L*0.16} {L*0.75} 0 {L} C {-L*0.16} {L*0.75} {-L*0.22} {L*0.2} 0 0Z" fill="url(#leaf)"/>'
            f'<path d="M0 2 V{L*0.92}" stroke="#a6c27a" stroke-width="1" opacity=".7"/></g>')
dec += f'<line x1="{P(-1.78, PH1+0.42, ZF-0.06)[0]:.1f}" y1="{P(-1.78, PH1+0.42, ZF-0.06)[1]:.1f}" x2="{P(1.78, PH1+0.42, ZF-0.06)[0]:.1f}" y2="{P(1.78, PH1+0.42, ZF-0.06)[1]:.1f}" stroke="#c9a14f" stroke-width="3"/>'
# marigold garlands spiralling the front pillars
for side in (-1, 1):
    for t in np.linspace(0, 1, 70):
        h = PH0 + 0.3 + t * (PH1 - PH0 - 0.65)
        uu = side * UP + 0.12 * math.sin(t * 18)
        p = P(uu, h, ZF - 0.12)
        if math.cos(t * 18) < -0.2:
            continue
        dec += f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="9" fill="url(#{"mari" if int(t*70)%4 else "jas"})"/>'


# ======================= LAYER: banana plants =======================
def banana(u, z, side):
    o = ''
    s = F / z
    b = P(u, 0, z); t = P(u, 2.1, z)
    sw_ = 0.17 * s
    o += f'<path d="M{b[0]-sw_/2:.1f} {b[1]:.1f} Q{b[0]-sw_*0.55:.1f} {(b[1]+t[1])/2:.1f} {t[0]-sw_*0.3:.1f} {t[1]:.1f} L{t[0]+sw_*0.3:.1f} {t[1]:.1f} Q{b[0]+sw_*0.55:.1f} {(b[1]+t[1])/2:.1f} {b[0]+sw_/2:.1f} {b[1]:.1f}Z" fill="url(#bstem)"/>'
    # leaf sheath stripes on the pseudostem
    for k in range(7):
        yy = b[1] - (k + 0.5) * (b[1] - t[1]) / 7
        o += f'<path d="M{b[0]-sw_*0.4:.1f} {yy:.1f} q{sw_*0.4:.1f} {-sw_*0.25:.1f} {sw_*0.8:.1f} 0" stroke="#3c5c25" stroke-width="1.6" fill="none" opacity=".45"/>'
    # leaves: (start height m, angle deg from vertical [+ = outward], length m, droop)
    spec = [(2.05, 8, 1.35, 0.15), (1.95, 32, 1.55, 0.35), (1.85, 58, 1.6, 0.7), (1.7, 85, 1.45, 1.0),
            (2.0, -18, 1.3, 0.25), (1.9, -42, 1.35, 0.55), (1.75, -70, 1.2, 0.9), (2.1, 18, 1.1, 0.05)]
    for (hs, ang, Lm, droop) in spec:
        st = P(u, hs, z)
        a = math.radians(ang * side - 90)
        Lp = Lm * s
        dx, dy = math.cos(a), math.sin(a)
        # midrib: rises along direction, then droops under gravity
        p0 = st
        p1 = (st[0] + dx * Lp * 0.5, st[1] + dy * Lp * 0.5 - Lp * 0.05)
        p2 = (st[0] + dx * Lp * 0.95, st[1] + dy * Lp * 0.75 + droop * Lp * 0.55)
        wv = 0.2 * s
        s1, s2, ribs = [], [], []
        for tt in np.linspace(0, 1, 30):
            px = (1 - tt) ** 2 * p0[0] + 2 * (1 - tt) * tt * p1[0] + tt * tt * p2[0]
            py = (1 - tt) ** 2 * p0[1] + 2 * (1 - tt) * tt * p1[1] + tt * tt * p2[1]
            tx_ = 2 * (1 - tt) * (p1[0] - p0[0]) + 2 * tt * (p2[0] - p1[0])
            ty_ = 2 * (1 - tt) * (p1[1] - p0[1]) + 2 * tt * (p2[1] - p1[1])
            nl = math.hypot(tx_, ty_) + 1e-6
            nx, ny = -ty_ / nl, tx_ / nl
            prof = min(1, tt / 0.12) * (1 if tt < 0.85 else math.sqrt(max(0, 1 - ((tt - 0.85) / 0.15) ** 2)))
            ww = wv * prof
            s1.append((px + nx * ww, py + ny * ww)); s2.append((px - nx * ww * 0.85, py - ny * ww * 0.85))
            ribs.append((px, py, nx, ny, ww))
        o += poly(s1 + s2[::-1], fill='url(#banana)')
        # lateral veins + a couple of natural tears
        for k, (px, py, nx, ny, ww) in enumerate(ribs[2:-2]):
            if k % 2 == 0:
                o += f'<path d="M{px:.1f} {py:.1f} l{nx*ww:.1f} {ny*ww+ww*0.15:.1f}" stroke="#2f5420" stroke-width=".8" opacity=".35"/>'
            if k in (9, 17):
                o += f'<path d="M{px+nx*ww*0.25:.1f} {py+ny*ww*0.25:.1f} l{nx*ww*0.8:.1f} {ny*ww*0.8:.1f}" stroke="#20381a" stroke-width="2" opacity=".6"/>'
        o += f'<path d="M{p0[0]:.1f} {p0[1]:.1f} Q{p1[0]:.1f} {p1[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}" stroke="#d3e0a6" stroke-width="{0.018*s:.1f}" fill="none"/>'
    # a hanging banana bunch with purple bud on the outer side
    bb = P(u + side * 0.22, 1.5, z)
    for k in range(12):
        o += f'<ellipse cx="{bb[0]+(k%4-1.5)*0.045*s:.1f}" cy="{bb[1]+k//4*0.07*s:.1f}" rx="{0.025*s:.1f}" ry="{0.06*s:.1f}" fill="#93b03c" stroke="#4d6a1c" stroke-width="1"/>'
    bud = (bb[0], bb[1] + 0.3 * s)
    o += f'<ellipse cx="{bud[0]:.1f}" cy="{bud[1]:.1f}" rx="{0.04*s:.1f}" ry="{0.08*s:.1f}" fill="#6e2a3c"/>'
    return o

ban = banana(-2.0, 4.7, -1) + banana(2.0, 4.7, 1)

# ======================= LAYER: lamps =======================
lamps = []   # (x, y, size, group)
lb = ''
fl = ''


def deepam(u, z, h=0.0, group=0):
    global lb, fl
    c = P(u, h, z)
    s = 0.13 * F / z
    lb += f'<ellipse cx="{c[0]:.1f}" cy="{c[1]:.1f}" rx="{s*0.62:.1f}" ry="{s*0.16:.1f}" fill="#3b2a12" opacity=".5"/>'
    lb += f'<path d="M{c[0]-s*0.22:.1f} {c[1]:.1f} L{c[0]-s*0.12:.1f} {c[1]-s*0.35:.1f} L{c[0]+s*0.12:.1f} {c[1]-s*0.35:.1f} L{c[0]+s*0.22:.1f} {c[1]:.1f}Z" fill="url(#gold)"/>'
    lb += f'<path d="M{c[0]-s*0.55:.1f} {c[1]-s*0.42:.1f} Q{c[0]:.1f} {c[1]-s*0.05:.1f} {c[0]+s*0.55:.1f} {c[1]-s*0.42:.1f}Z" fill="url(#goldv)"/>'
    lb += f'<ellipse cx="{c[0]:.1f}" cy="{c[1]-s*0.42:.1f}" rx="{s*0.55:.1f}" ry="{s*0.1:.1f}" fill="#f4d78a"/>'
    fx, fy = c[0] + s * 0.32, c[1] - s * 0.48
    fl += f'<path d="M{fx-s*0.07:.1f} {fy:.1f} Q{fx:.1f} {fy-s*0.55:.1f} {fx+s*0.02:.1f} {fy-s*0.62:.1f} Q{fx+s*0.1:.1f} {fy-s*0.2:.1f} {fx+s*0.07:.1f} {fy:.1f}Z" fill="#fff4c4"/>'
    lamps.append((fx, fy - s * 0.25, s, group))


def kundulu(u, z, group):
    """Tall standing brass lamp with five wicks."""
    global lb
    b = P(u, 0, z); s = F / z
    top = P(u, 1.35, z)
    lb += f'<ellipse cx="{b[0]:.1f}" cy="{b[1]:.1f}" rx="{0.22*s:.1f}" ry="{0.05*s:.1f}" fill="#2b1e0c" opacity=".55"/>'
    lb += f'<path d="M{b[0]-0.2*s:.1f} {b[1]:.1f} Q{b[0]:.1f} {b[1]-0.22*s:.1f} {b[0]+0.2*s:.1f} {b[1]:.1f}Z" fill="url(#goldv)"/>'
    lb += f'<rect x="{b[0]-0.022*s:.1f}" y="{top[1]:.1f}" width="{0.044*s:.1f}" height="{b[1]-top[1]-0.1*s:.1f}" fill="url(#gold)"/>'
    for hh in (0.35, 0.7, 1.05):
        p = P(u, hh, z)
        lb += f'<ellipse cx="{p[0]:.1f}" cy="{p[1]:.1f}" rx="{0.05*s:.1f}" ry="{0.03*s:.1f}" fill="url(#pot)"/>'
    lb += f'<path d="M{top[0]-0.17*s:.1f} {top[1]:.1f} Q{top[0]:.1f} {top[1]+0.1*s:.1f} {top[0]+0.17*s:.1f} {top[1]:.1f}Z" fill="url(#goldv)"/>'
    lb += f'<ellipse cx="{top[0]:.1f}" cy="{top[1]:.1f}" rx="{0.17*s:.1f}" ry="{0.035*s:.1f}" fill="#f2d385"/>'
    # finial (parrot-like crown simplified to a bud)
    lb += f'<path d="M{top[0]-0.03*s:.1f} {top[1]:.1f} L{top[0]:.1f} {top[1]-0.22*s:.1f} L{top[0]+0.03*s:.1f} {top[1]:.1f}Z" fill="url(#gold)"/>'
    lb += f'<circle cx="{top[0]:.1f}" cy="{top[1]-0.24*s:.1f}" r="{0.03*s:.1f}" fill="url(#pot)"/>'
    for k, du in enumerate((-0.15, -0.075, 0.075, 0.15)):
        global fl
        fx, fy = P(u + du, 1.36, z)
        ss = 0.1 * s
        fl += f'<path d="M{fx-ss*0.09:.1f} {fy:.1f} Q{fx:.1f} {fy-ss*0.7:.1f} {fx+ss*0.02:.1f} {fy-ss*0.8:.1f} Q{fx+ss*0.12:.1f} {fy-ss*0.25:.1f} {fx+ss*0.09:.1f} {fy:.1f}Z" fill="#fff4c4"/>'
        lamps.append((fx, fy - ss * 0.35, ss, group))


# ignition order: path rows from front to back (groups 0..6), kundulu (7), dais row (8)
for i, z in enumerate(np.linspace(2.45, 3.95, 7)):
    deepam(-0.95, z, 0, i)
    deepam(0.95, z, 0, i)
kundulu(-1.15, 4.05, 7)
kundulu(1.15, 4.05, 7)
for u in np.linspace(-1.75, 1.75, 9):
    deepam(u, 4.6, PH0 + 0.002, 8)

# ======================= render layers =======================
L = {}
for name, body in [('far', far), ('ground', gnd), ('mandapam', md), ('decor', dec), ('banana', ban), ('lampbody', lb), ('flame', fl)]:
    L[name] = render_svg(svgdoc(body), W, H, 'scene_' + name, transparent=True)
np.save(os.path.join(TMP, 'lamps.npy'), np.array(lamps, dtype=np.float32))
print('lamps', len(lamps))

import pickle
pickle.dump(L, open(os.path.join(TMP, 'scene_layers.pkl'), 'wb'))
