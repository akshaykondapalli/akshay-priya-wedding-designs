"""Composite the scene layers into the realistic and watercolor renders."""
from common import *
import pickle, json, sys

S = 1800; W = H = S; HZ = 820
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
L = pickle.load(open(os.path.join(TMP, 'scene_layers.pkl'), 'rb'))
lamps = np.load(os.path.join(TMP, 'lamps.npy'))


def over(base, layer, k=1.0):
    a = layer[..., 3:4] * k
    return base * (1 - a) + layer[..., :3] * a


# ---------------- sky ----------------
t = np.clip(y / HZ, 0, 1)[..., None]
c0 = np.array([0.10, 0.22, 0.27]); c1 = np.array([0.36, 0.33, 0.42]); c2 = np.array([0.86, 0.52, 0.45]); c3 = np.array([1.0, 0.76, 0.50])
sky = np.where(t < 0.45, c0 + (c1 - c0) * (t / 0.45), np.where(t < 0.8, c1 + (c2 - c1) * ((t - 0.45) / 0.35), c2 + (c3 - c2) * ((t - 0.8) / 0.2)))
# sun glow just below horizon behind the mandapam
sg = np.exp(-(((x - 900) / 700) ** 2 + ((y - HZ) / 260) ** 2))
sky = sky + sg[..., None] * np.array([0.35, 0.20, 0.06])
# soft streak clouds lit from below
cl = fbm(H, W, 240, 5, seed=301)
cl = ndi.gaussian_filter(cl, (6, 40))
cmask = smoothstep(0.55, 0.75, cl) * smoothstep(80, 420, y) * (1 - smoothstep(640, 800, y))
sky = sky * (1 - cmask[..., None] * 0.5) + cmask[..., None] * 0.5 * np.array([0.95, 0.62, 0.55])
ground_col = np.array([0.55, 0.43, 0.32])
gt = np.clip((y - HZ) / (H - HZ), 0, 1)[..., None]
ground = ground_col * (0.55 + 0.45 * gt)
# stone flags texture on ground
gz = 1100 * 1.6 / np.maximum(y - HZ, 1)  # depth per row
gu = (x - 900) * gz / 1100
tile = (np.abs(((gu / 0.6) % 1) - 0.5) < 0.485) & (np.abs(((gz / 0.6) % 1) - 0.5) < 0.48)
gn = fbm(H, W, 30, 3, seed=302)
ground = ground * (0.86 + 0.14 * gn[..., None]) * np.where(tile, 1.0, 0.82)[..., None]
base = np.where((y < HZ)[..., None], sky, ground)
np.save(os.path.join(TMP, 'sky_base.npy'), base.astype(np.float32))

# ---------------- flat composite (daylight-neutral; used for watercolor) ----------------
flat = base.copy()
for k in ['far', 'ground', 'mandapam', 'decor', 'banana', 'lampbody']:
    flat = over(flat, L[k])

# depth map (rough): far=1, mandapam ~0.5, near 0
depth = np.where(y < HZ, 1.0, np.clip(1 - (y - HZ) / (H - HZ), 0, 1) * 0.8)
depth = np.where(L['far'][..., 3] > 0.5, 0.95, depth)
depth = np.where((L['mandapam'][..., 3] + L['decor'][..., 3]) > 0.5, 0.45, depth)
depth = np.where(L['banana'][..., 3] > 0.5, 0.42, depth)

# =================== REALISTIC ===================
# albedo composite with material texture
alb = base.copy()
alb = over(alb, L['far'])
alb = over(alb, L['ground'])
stone_tex = (0.9 + 0.2 * fbm(H, W, 5, 3, seed=330))[..., None]
# contact / ambient-occlusion shadows cast on the ground by everything standing on it
occ = (L['mandapam'][..., 3] + L['banana'][..., 3] + L['lampbody'][..., 3] * 0.6)
occ = np.clip(occ, 0, 1)
occ_s = ndi.shift(ndi.gaussian_filter(occ, 14), (18, 0), order=1)
ground_mask = ((y > HZ) & (L['far'][..., 3] < 0.5))[..., None]
alb = alb * (1 - ground_mask * np.clip(occ_s, 0, 1)[..., None] * 0.55)
for k in ['mandapam', 'decor', 'banana', 'lampbody']:
    lay = L[k].copy()
    if k == 'mandapam':
        lay[..., :3] *= stone_tex
    alb = over(alb, lay)

sky_m = ((y < HZ) & (L['far'][..., 3] < 0.3) & (L['mandapam'][..., 3] < 0.3) & (L['decor'][..., 3] < 0.3) & (L['banana'][..., 3] < 0.3)).astype(np.float32)[..., None]

# lamp light accumulation (HDR)
light = np.zeros((H, W), np.float32)
for (lx, ly, s, g) in lamps:
    r2 = (x - lx) ** 2 + ((y - ly) * 1.3) ** 2
    k = (s * 3.5) ** 2
    light += (np.exp(-r2 / (2 * (s * 3.0) ** 2)) * 0.9 + k / (r2 + k) * 0.08) * (0.3 if g == 7 else 0.12 if g == 8 else 0.42)
# warm light spilling from the canopy interior (the drape glows)
light += 0.7 * np.exp(-(((x - 900) / 280) ** 2 + ((y - 680) / 220) ** 2))
print('light pct', np.percentile(light, [10, 50, 90, 99]))
light = light[..., None]
ambient = np.array([0.26, 0.27, 0.38])          # dusk sky fill, cool
warm = np.array([1.0, 0.66, 0.34])
hdr = alb * (ambient + light * warm * 1.1)
# rim light from the glowing sky on silhouettes (top edges)
rim = np.clip(ndi.shift(1 - sky_m[..., 0], (4, 0), order=0) - (1 - sky_m[..., 0]), 0, 1)
hdr = hdr * (1 - sky_m) + base * 1.05 * sky_m
# far palms and wall sit in dusk haze
fg_a = np.clip(L['mandapam'][..., 3] + L['decor'][..., 3] + L['banana'][..., 3] + L['lampbody'][..., 3] + L['ground'][..., 3], 0, 1)
farm = (L['far'][..., 3:4] > 0) * (y < 1000)[..., None] * (1 - fg_a)[..., None]
hdr = hdr * (1 - farm * 0.35) + farm * 0.35 * np.array([0.62, 0.42, 0.40])
# flames (emissive)
fl = L['flame']
flame = fl[..., 3:4] * np.array([2.4, 2.0, 1.3])
hdr = hdr * (1 - fl[..., 3:4]) + flame
halo = np.zeros((H, W), np.float32)
for (lx, ly, s, g) in lamps:
    r2 = (x - lx) ** 2 + (y - ly) ** 2
    kk = 0.45 if g == 7 else 0.6 if g == 8 else 0.55
    halo += (np.exp(-r2 / (2 * (s * 0.55) ** 2)) * 1.6 + np.exp(-r2 / (2 * (s * 1.8) ** 2)) * 0.35) * kk
hdr = hdr + halo[..., None] * np.array([1.0, 0.72, 0.38])
np.save(os.path.join(TMP, 'halo.npy'), halo)
# bloom from HDR highlights
bright = np.clip(hdr - 1.1, 0, None)
bloom = blur(bright, 6) * 0.8 + blur(bright, 24) * 0.7 + blur(flame, 10) * 0.6 + blur(flame, 40) * 0.4
hdr = hdr + bloom * np.array([1.0, 0.7, 0.4])
# atmospheric glow around the mandapam
hdr = hdr + np.exp(-(((x - 900) / 600) ** 2 + ((y - 760) / 380) ** 2))[..., None] * np.array([0.10, 0.06, 0.03])
# tone map (filmic-ish)
expo = 1.6
real = 1 - np.exp(-hdr * expo)
# depth of field on the far layer
far_mask = blur((depth > 0.9).astype(np.float32)[..., None], 3)
real = real * (1 - far_mask) + blur(real, 2.0) * far_mask
# foreground bokeh (out-of-focus jasmine and marigold petals) at the lower corners
bok = np.zeros((H, W, 3), np.float32)
r3 = np.random.default_rng(310)
for i in range(40):
    side = -1 if i % 2 else 1
    bx = 900 + side * r3.uniform(600, 1050)
    by = r3.uniform(1500, 1900)
    rr = r3.uniform(26, 64)
    colr = [np.array([1.0, 0.97, 0.9]), np.array([1.0, 0.62, 0.15]), np.array([0.95, 0.42, 0.28])][r3.integers(0, 3)]
    d = np.sqrt((x - bx) ** 2 + (y - by) ** 2)
    disc = smoothstep(rr, rr * 0.88, d) * (0.6 + 0.4 * smoothstep(rr * 0.6, rr, d))
    bok += disc[..., None] * colr * r3.uniform(0.18, 0.4)
bok = blur(bok, 2.0)
real = screen(real, np.clip(bok, 0, 1))
vig = 1 - 0.5 * smoothstep(0.5, 1.3, np.sqrt(((x - 900) / 900) ** 2 + ((y - 880) / 900) ** 2))
real = np.clip(real * vig[..., None], 0, 1)
real = real + grain(H, W, 0.018, seed=311)
save(real, 'scene-real.webp', q=80)
save(real, 'scene-real-1100.webp', q=78, size=(1100, 1100))

# =================== WATERCOLOR ===================
wc = flat.copy()
# paint simplification: blur + slight posterise in luminance
wc = blur(wc, 1.6)
# brighten & desaturate toward paper (washes are transparent)
paper = np.array([0.965, 0.935, 0.875])
lum = (wc @ np.array([0.3, 0.59, 0.11]))[..., None]
wc = wc * 0.9 + lum * 0.1
wc = np.clip((wc - 0.5) * 1.15 + 0.55, 0, 1)
wc = paper * (1 - 0.7 * (1 - wc))  # lift
wc = wc * np.array([1.03, 1.0, 0.94])
# wobble (paint does not follow the ruler)
dx = (fbm(H, W, 22, 3, seed=320) - .5) * 9
dy = (fbm(H, W, 22, 3, seed=321) - .5) * 9
wc = np.stack([ndi.map_coordinates(wc[..., c], [y + dy, x + dx], order=1, mode='reflect') for c in range(3)], -1)
# edge darkening along colour boundaries
lum = wc @ np.array([0.3, 0.59, 0.11])
gm = ndi.gaussian_gradient_magnitude(lum, 1.3)
edge = smoothstep(0.02, 0.10, gm)
wc = wc * (1 - edge[..., None] * 0.34)
# wash mottling: uneven pigment density inside flat areas
mott = fbm(H, W, 45, 4, 0.55, seed=327)
wc = paper - (paper - wc) * (0.78 + 0.45 * mott[..., None])
# lifted highlights / blooms
lift = smoothstep(0.7, 0.78, fbm(H, W, 90, 3, seed=328))
wc = wc * (1 - lift[..., None] * 0.25) + paper * lift[..., None] * 0.25
# sky as wet-in-wet wash with blooms
skym = (y < HZ + 10)[..., None] * (1 - L['far'][..., 3:4]) * (1 - L['mandapam'][..., 3:4]) * (1 - L['decor'][..., 3:4]) * (1 - L['banana'][..., 3:4])
skyw = blur(wc, 18) * (0.9 + 0.2 * fbm(H, W, 160, 4, seed=322)[..., None])
wc = wc * (1 - skym) + skyw * skym
# granulation + paper texture
ph = fbm(H, W, 6, 3, seed=323) * 0.6 + fbm(H, W, 40, 3, seed=324) * 0.4
wc = wc * (0.9 + 0.16 * ph[..., None])
# light pencil/ink linework from the flat render
inkl = smoothstep(0.06, 0.2, ndi.gaussian_gradient_magnitude(flat @ np.array([0.3, 0.59, 0.11]), 0.9))
inkl *= (0.6 + 0.4 * fbm(H, W, 8, 2, seed=325))
wc = wc * (1 - inkl[..., None] * 0.35) + np.array([0.35, 0.25, 0.18]) * inkl[..., None] * 0.35
# unlit lamps: no flames (they ignite in the browser)
# paper vignette (white margins bleeding in)
edgev = smoothstep(0.75, 1.25, np.sqrt(((x - 900) / 900) ** 2 + ((y - 900) / 900) ** 2))
wc = wc * (1 - edgev[..., None] * 0.6) + paper * edgev[..., None] * 0.6
wc += grain(H, W, 0.01, seed=326)
save(wc, 'scene-water.webp', q=80)
save(wc, 'scene-water-1100.webp', q=78, size=(1100, 1100))

# lamp metadata (normalised) for the shader
out = [{'x': round(float(lx) / W, 4), 'y': round(float(ly) / H, 4), 's': round(float(s) / W, 4), 'g': int(g)} for (lx, ly, s, g) in lamps]
json.dump(out, open('/home/claude/site/fusion/img/lamps.json', 'w'))
print('ok')
