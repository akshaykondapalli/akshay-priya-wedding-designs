import math
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from common import *
import textures

OUT = '/home/claude/site/heritage/img/'
W, H = 1200, 1500
# key points (also used in the HTML SVG overlay — keep in sync)
A0 = (230, 330)    # start of journey one (gold)
B0 = (990, 520)    # start of journey two (oxblood)
MEET = (640, 1010)  # where they converge


def blob(x, y, cx, cy, rx, ry):
    return np.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))


def make():
    rng = np.random.default_rng(42)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    n = noise(H, W, 200, 7, 0.6, rng)
    field = n * 1.15
    field += 0.55 * blob(x, y, 300, 380, 300, 260)
    field += 0.50 * blob(x, y, 930, 560, 260, 300)
    field += 0.55 * blob(x, y, 640, 960, 170, 260)   # peninsula to the meet point
    field += 0.25 * blob(x, y, 640, 760, 380, 140)
    field -= 0.75 * blob(x, y, 620, 420, 150, 330)   # sea between the two
    field -= 0.35 * blob(x, y, 250, 1150, 260, 260)
    field -= 0.35 * blob(x, y, 1050, 1200, 250, 260)
    edge = np.minimum.reduce([x, y, W - x, H - y])
    field -= np.clip(1 - edge / 120, 0, 1) * 0.6
    land = field > 0.92
    land = ndi.binary_opening(land, iterations=2)
    # remove tiny islands except a few
    lab, k = ndi.label(land)
    sizes = ndi.sum(land, lab, range(1, k + 1))
    keep = np.isin(lab, np.where(sizes > 120)[0] + 1)
    land = keep
    landf = ndi.gaussian_filter(land.astype(np.float32), 1.0)

    par = textures.parchment(W, H, name='_tmp.webp', seed=19, out_size=(W, H))
    col = par.copy()
    ink = hexc('#3b2a1a')
    # land tint: warmer, slightly darker, with relief shading
    relief = noise(H, W, 70, 4, 0.5, rng)
    nrm = normals(relief * landf, 30)
    sh = light(nrm, (-0.5, -0.6, 0.6))
    col = col * (1 - landf[..., None] * 0.10) + hexc('#efdcae') * landf[..., None] * 0.10
    col = col * (1 - landf[..., None] * (0.07 * (1 - sh[..., None])))
    # sea: faint blue-green wash
    sea = 1 - landf
    col = col * (1 - sea[..., None] * 0.20) + hexc('#8e9f88') * sea[..., None] * 0.20
    # waterlining
    dist = ndi.distance_transform_edt(~land)
    wl = np.zeros_like(dist)
    for k_ in range(1, 6):
        d0 = k_ * 11
        wl += np.clip(1 - np.abs(dist - d0) / 0.9, 0, 1) * (1 - k_ / 6.5)
    col -= wl[..., None] * 0.18 * (ink * 0 + 1) * 0.9
    # coastline: double ink line
    coast = np.clip(1 - np.abs(dist - 0.8) / 1.2, 0, 1) * (~land)
    ldist = ndi.distance_transform_edt(land)
    coast = np.maximum(coast, np.clip(1 - np.abs(ldist - 1) / 1.1, 0, 1))
    col = col * (1 - coast[..., None] * 0.75) + ink * coast[..., None] * 0.75
    # sea stippling
    stip = (rng.random((H, W)) < 0.010 * sea * np.clip(dist / 200, 0.1, 1))
    stip = ndi.binary_dilation(stip, iterations=0) if False else stip
    col[stip] = col[stip] * 0.6
    # mountains: little hatched carets on land
    im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    inkc = (70, 50, 32)
    for _ in range(900):
        px, py = rng.integers(60, W - 60), rng.integers(60, H - 60)
        if not land[py, px] or ldist[py, px] < 18 or relief[py, px] < 0.45:
            continue
        s = rng.uniform(9, 16)
        d.line([(px - s, py + s * 0.6), (px, py - s * 0.6), (px + s, py + s * 0.6)], fill=inkc, width=2)
        for j in range(3):
            d.line([(px + j * 2.5, py - s * 0.4 + j * 3), (px + s * 0.6 + j, py + s * 0.6)], fill=(90, 66, 44), width=1)
    # rhumb lines from two compass roses
    for (rx, ry) in [(170, 1230), (1040, 230)]:
        for i in range(32):
            a = i / 32 * 2 * math.pi
            d.line([(rx, ry), (rx + math.cos(a) * 1800, ry + math.sin(a) * 1800)],
                   fill=(110, 84, 56) if i % 4 else (120, 40, 36), width=1)
    im = Image.fromarray(np.asarray(im))
    arr = np.asarray(im).astype(np.float32) / 255
    # fade rhumb lines a lot: blend with pre-line image
    pre = np.clip(col, 0, 1)
    arr = pre * 0.72 + arr * 0.28
    im = Image.fromarray((arr * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for (rx, ry, R) in [(170, 1230, 95), (1040, 230, 80)]:
        rose(d, rx, ry, R)
    # graticule border with degree ticks
    d.rectangle([28, 28, W - 28, H - 28], outline=inkc, width=3)
    d.rectangle([40, 40, W - 40, H - 40], outline=inkc, width=1)
    for i in range(0, W - 80, 30):
        if (i // 30) % 2 == 0:
            d.rectangle([40 + i, 30, 40 + i + 30, 38], fill=inkc)
            d.rectangle([40 + i, H - 38, 40 + i + 30, H - 30], fill=inkc)
    for i in range(0, H - 80, 30):
        if (i // 30) % 2 == 0:
            d.rectangle([30, 40 + i, 38, 40 + i + 30], fill=inkc)
            d.rectangle([W - 38, 40 + i, W - 30, 40 + i + 30], fill=inkc)
    arr = np.asarray(im).astype(np.float32) / 255
    arr = grain(arr, 0.01)
    save(arr, OUT + 'map.webp', q=76, size=(900, 1125))
    import os; os.remove(OUT + '_tmp.webp')


def rose(d, cx, cy, R):
    inkc = (70, 50, 32)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=inkc, width=2)
    d.ellipse([cx - R * 0.86, cy - R * 0.86, cx + R * 0.86, cy + R * 0.86], outline=inkc, width=1)
    for i in range(8):
        a = i / 8 * 2 * math.pi - math.pi / 2
        L = R * (1.15 if i % 2 == 0 else 0.7)
        tip = (cx + math.cos(a) * L, cy + math.sin(a) * L)
        l1 = (cx + math.cos(a - 0.35) * L * 0.2, cy + math.sin(a - 0.35) * L * 0.2)
        l2 = (cx + math.cos(a + 0.35) * L * 0.2, cy + math.sin(a + 0.35) * L * 0.2)
        d.polygon([tip, l1, (cx, cy)], fill=(120, 40, 36) if i == 0 else inkc)
        d.polygon([tip, l2, (cx, cy)], fill=(222, 205, 168))
        d.line([tip, l2, (cx, cy)], fill=inkc, width=1)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=inkc)


if __name__ == '__main__':
    make()
