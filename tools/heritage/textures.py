import sys, math
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from common import *

OUT = '/home/claude/site/heritage/img/'


def wood(w=1400, h=1800):
    """Dark rosewood table, grain running horizontally."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    def aniso(sy, sx, k=1):
        r = ndi.gaussian_filter(RNG.random((h, w)).astype(np.float32), (sy, sx), mode='wrap')
        r = (r - r.mean()) / (r.std() + 1e-6)
        return r
    warp = (noise(h, w, 500, 3) - 0.5) * 120
    # warp coordinates for figure
    yy = np.clip(y + warp, 0, h - 1).astype(int)
    f1 = aniso(1.2, 90); f2 = aniso(4, 260); f3 = aniso(14, 500); f0 = aniso(0.5, 25)
    fig = (0.25 * f0 + 0.4 * f1 + 0.6 * f2 + 0.7 * f3)
    fig = fig[yy, np.arange(w)[None, :].repeat(h, 0)]
    t = 0.5 + 0.16 * fig
    col = ramp(np.clip(t, 0, 1), [(0, '#0a0403'), (0.35, '#24100a'), (0.55, '#3d1b10'), (0.75, '#5c2b17'), (1, '#7a3d22')])
    col *= 0.7
    col = grain(col, 0.01)
    save(col, OUT + 'wood.webp', q=72, size=(1000, 1286))


def leather_height(w, h):
    big = noise(h, w, 60, 5, 0.55)
    cells = noise(h, w, 6, 3, 0.6)
    # pebble grain: ridges around cells
    peb = np.abs(cells - 0.5) * 2
    return big * 0.6 + (1 - peb) * 0.35 + noise(h, w, 2, 1) * 0.05


def cover(w=900, h=1180):
    """Green leather cover with gold tooling, compass rose and foil title."""
    H = leather_height(w, h)
    # tooling heightmap (debossed -> negative)
    ss = 2
    def tooling(d, s):
        m = 46 * s
        d.rounded_rectangle([m, m, w * s - m, h * s - m], radius=10 * s, outline=255, width=int(3 * s))
        m2 = 62 * s
        d.rounded_rectangle([m2, m2, w * s - m2, h * s - m2], radius=6 * s, outline=255, width=int(1.4 * s))
        # corner fleurons (simple lotus-like petals)
        for (cx, cy, sx, sy) in [(m2, m2, 1, 1), (w * s - m2, m2, -1, 1), (m2, h * s - m2, 1, -1), (w * s - m2, h * s - m2, -1, -1)]:
            for k in range(3):
                r = (26 + k * 16) * s
                d.arc([cx - r, cy - r, cx + r, cy + r], 0 if sx > 0 and sy > 0 else (90 if sx < 0 and sy > 0 else (270 if sx > 0 else 180)),
                      (90 if sx > 0 and sy > 0 else (180 if sx < 0 and sy > 0 else (360 if sx > 0 else 270))), fill=255, width=int(1.5 * s))
            d.ellipse([cx + sx * 10 * s - 4 * s, cy + sy * 10 * s - 4 * s, cx + sx * 10 * s + 4 * s, cy + sy * 10 * s + 4 * s], fill=255)
        # dotted inner rule
        m3 = 78 * s
        for xx in range(int(m3 + 20 * s), int(w * s - m3 - 10 * s), int(14 * s)):
            for yy in (m3, h * s - m3):
                d.ellipse([xx - 1.6 * s, yy - 1.6 * s, xx + 1.6 * s, yy + 1.6 * s], fill=255)
        for yy in range(int(m3 + 20 * s), int(h * s - m3 - 10 * s), int(14 * s)):
            for xx in (m3, w * s - m3):
                d.ellipse([xx - 1.6 * s, yy - 1.6 * s, xx + 1.6 * s, yy + 1.6 * s], fill=255)
    gold_lines = mask_from_draw(w, h, tooling, ss)

    # compass rose
    cx, cy, R = w / 2, h * 0.585, 150
    def compass(d, s):
        C = (cx * s, cy * s)
        d.ellipse([C[0] - R * s, C[1] - R * s, C[0] + R * s, C[1] + R * s], outline=255, width=int(2.2 * s))
        d.ellipse([C[0] - (R - 12) * s, C[1] - (R - 12) * s, C[0] + (R - 12) * s, C[1] + (R - 12) * s], outline=255, width=int(1 * s))
        for i in range(64):
            a = i / 64 * 2 * math.pi
            r0 = R - 12 if i % 4 else R - 22
            d.line([C[0] + math.cos(a) * r0 * s, C[1] + math.sin(a) * r0 * s, C[0] + math.cos(a) * R * s, C[1] + math.sin(a) * R * s], fill=255, width=int(1.1 * s))
        # 16 points
        for i in range(16):
            a = i / 16 * 2 * math.pi - math.pi / 2
            L = [R * 1.18, R * 0.55, R * 0.82, R * 0.5][i % 4]
            wdt = [0.13, 0.09, 0.11, 0.08][i % 4]
            tip = (C[0] + math.cos(a) * L * s, C[1] + math.sin(a) * L * s)
            l1 = (C[0] + math.cos(a - wdt * 3.2) * L * 0.22 * s, C[1] + math.sin(a - wdt * 3.2) * L * 0.22 * s)
            l2 = (C[0] + math.cos(a + wdt * 3.2) * L * 0.22 * s, C[1] + math.sin(a + wdt * 3.2) * L * 0.22 * s)
            d.polygon([tip, l1, C], fill=255 if i % 4 == 0 else 200)
            d.polygon([tip, l2, C], fill=150 if i % 4 == 0 else 120)
        d.ellipse([C[0] - 9 * s, C[1] - 9 * s, C[0] + 9 * s, C[1] + 9 * s], fill=255)
    comp = mask_from_draw(w, h, compass, ss)

    # title text
    def title(d, s):
        f1 = font('csc', int(92 * s))
        f2 = font('csc', int(34 * s))
        f3 = font('cgi', int(36 * s))
        for txt, f, yy in [('THE ATLAS', f1, 175), ('OF US', f1, 272)]:
            tw = d.textlength(txt, font=f)
            d.text(((w * s - tw) / 2, yy * s), txt, font=f, fill=255)
        tw = d.textlength('AKSHAY  &  PRIYA', font=f2)
        d.text(((w * s - tw) / 2, 905 * s), 'AKSHAY  &  PRIYA', font=f2, fill=255)
        tw = d.textlength('a journey to one destination', font=f3)
        d.text(((w * s - tw) / 2, 958 * s), 'a journey to one destination', font=f3, fill=255)
        d.line([(w * s / 2 - 70 * s, 395 * s), (w * s / 2 + 70 * s, 395 * s)], fill=255, width=int(1.5 * s))
        d.ellipse([w * s / 2 - 4 * s, 391 * s, w * s / 2 + 4 * s, 399 * s], fill=255)
    txt = mask_from_draw(w, h, title, ss)

    gold = np.clip(gold_lines + comp + txt, 0, 1)
    # Wear: gold rubbed off in places
    wear = noise(h, w, 30, 4)
    goldv = gold * np.clip((wear - 0.18) * 3, 0.25, 1)
    deboss = ndi.gaussian_filter(gold, 1.2)
    height = H * 1.0 - deboss * 1.6
    # edge rounding: leather rolls over board edges
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    ed = np.minimum.reduce([x, y, w - 1 - x, h - 1 - y])
    roll = np.clip(ed / 14, 0, 1) ** 0.7
    height = height + roll * 1.6
    n = normals(height, 2.2)
    L = (-0.45, -0.55, 0.7)
    dif = light(n, L)
    sp = spec(n, L, 18)
    base_t = noise(h, w, 140, 4)
    leather = ramp(base_t, [(0, '#0b2219'), (0.5, '#143628'), (1, '#1f4a37')])
    # rub/wear lighter at edges and corners
    rub = np.clip(1 - ed / 60, 0, 1) ** 2 * (0.5 + 0.5 * noise(h, w, 12, 3))
    leather = leather * (1 - rub[..., None] * 0.35) + hexc('#3c4a35') * rub[..., None] * 0.35
    col = leather * (0.35 + 0.95 * dif[..., None]) + sp[..., None] * 0.10 * hexc('#d9c79a')
    # gold foil
    gn = normals(ndi.gaussian_filter(gold, 0.8) * 1.2 + noise(h, w, 3, 2) * 0.15, 3)
    gd = light(gn, L)
    gs = spec(gn, L, 30)
    gfoil = hexc('#6e4f1d') * (1 - gd[..., None]) + hexc('#d8b46a') * gd[..., None] + gs[..., None] * hexc('#fff1c9') * 0.9
    col = col * (1 - goldv[..., None]) + gfoil * goldv[..., None]
    # light falloff: warm lamp at left
    fall = np.exp(-(((x - w * 0.05) / (w * 1.1)) ** 2 + ((y - h * 0.25) / (h * 1.2)) ** 2))
    col *= (0.55 + 0.6 * fall[..., None])
    col *= np.array([1.05, 1.0, 0.92])
    col = grain(col, 0.012)
    save(col, OUT + 'atlas-cover.webp', q=82, size=(720, 944))
    # inside of cover: marbled endpaper
    marble(w, h)


def marble(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    v = x / w * 6 + noise(h, w, 200, 4) * 3
    for i in range(3):
        v += np.sin(y / (40 + i * 30) + v * 0.8) * (0.9 / (i + 1))
    comb = np.sin(x / 5.0 + noise(h, w, 80, 3) * 6) * 0.5
    t = (np.sin(v * 2.1 + comb) + 1) / 2
    t2 = (np.sin(v * 7.1 + y / 90 + comb * 2) + 1) / 2
    vein = np.clip(1 - np.abs(t - 0.5) * 14, 0, 1)
    col = ramp(t * 0.6 + noise(h, w, 120, 3) * 0.4, [(0, '#142c23'), (0.5, '#1f4033'), (1, '#2c4f3e')])
    col = col * (1 - vein[..., None]) + hexc('#b99a5c') * vein[..., None] * 0.8
    v2 = np.clip(1 - np.abs(t2 - 0.5) * 20, 0, 1) * 0.5
    col = col * (1 - v2[..., None]) + hexc('#5a1c1c') * v2[..., None]
    col = col * (0.8 + 0.2 * t2[..., None])
    col *= 0.85
    col = grain(col, 0.01)
    save(col, OUT + 'endpaper.webp', q=74, size=(540, 708))


def parchment(w=1200, h=1600, name='parchment.webp', seed=7, out_size=(900, 1200)):
    rng = np.random.default_rng(seed)
    base = noise(h, w, 300, 5, 0.55, rng)
    fib = noise(h, w, 8, 3, 0.5, rng)
    stains = noise(h, w, 180, 4, 0.6, rng)
    st = np.clip((stains - 0.62) * 4, 0, 1)
    ring = np.clip(1 - np.abs(stains - 0.6) * 40, 0, 1) * 0.5
    col = ramp(base * 0.7 + fib * 0.3, [(0, '#cdb68a'), (0.5, '#e3d1a8'), (1, '#efe2c2')])
    col = col * (1 - st[..., None] * 0.12) - ring[..., None] * 0.05
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    ed = np.minimum.reduce([x, y, w - 1 - x, h - 1 - y]) / min(w, h)
    burn = np.clip(1 - ed / 0.12, 0, 1) ** 2 * (0.6 + 0.4 * noise(h, w, 40, 3, 0.5, rng))
    col = col * (1 - burn[..., None] * 0.45) + hexc('#6b4a22') * burn[..., None] * 0.2
    col = grain(col, 0.012, rng)
    save(col, OUT + name, q=74, size=out_size)
    return col


if __name__ == '__main__':
    which = sys.argv[1:] or ['wood', 'cover', 'parchment']
    if 'wood' in which: wood()
    if 'cover' in which: cover()
    if 'parchment' in which: parchment()
