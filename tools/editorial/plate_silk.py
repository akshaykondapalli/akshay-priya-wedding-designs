from common import *

H, W = 2000, 1600
y, x = np.mgrid[0:H, 0:W].astype(np.float32)

# large drape folds (diagonal), with low-frequency warp
warp = (fbm(H, W, 3, 2, seed=11) - .5) * 260
t = (x * np.cos(1.05) + y * np.sin(1.05)) + warp
hf = (fbm(H, W, 3, 2, seed=4) - .5) * 5.0
mod = fbm(H, W, 2, 2, seed=9)
for k, a, ph in [(1 / 430, 1.1, 0.3), (1 / 260, .55, 1.7), (1 / 150, .18, .4)]:
    hf += a * mod * np.sin(2 * np.pi * k * t + ph)
for k, a, ph in [(1 / 700, .9, 0.1)]:
    hf += a * (1 - np.abs(np.sin(np.pi * k * (t * .97 + x * .08) + ph))) ** 4
hf = ndi.gaussian_filter(hf, 6)

# fabric coordinates follow the drape a little
u = x + ndi.gaussian_filter(hf, 8) * 6
v = y - ndi.gaussian_filter(hf, 8) * 14 + x * 0.22

# weave + raw-silk slubs
p = 5.0
weave = 0.5 + 0.25 * np.sin(2 * np.pi * u / p) * np.sign(np.sin(np.pi * v / p)) + 0.25 * np.sin(2 * np.pi * v / p)
r = np.random.default_rng(5)
slub_rows = ndi.zoom(r.standard_normal((H // 3 + 1, 30)).astype(np.float32), (3, W / 30), order=1)[:H, :W]
slub = np.clip(slub_rows, 1.2, 3) - 1.2
slub = ndi.gaussian_filter(slub, (0.8, 6))
# re-map slubs into fabric v space approx (cheap: sample rows by v)
vi = np.clip(v.astype(int) % H, 0, H - 1)
slub = slub[vi, np.clip(u.astype(int), 0, W - 1)]

# zari temple border band (in fabric coords)
band_c = 1240
bd = v - band_c
band = ((bd > -150) & (bd < 150)).astype(np.float32)
band = ndi.gaussian_filter(band, 1.2)
# temple triangles (gopuram) along top edge of band, and fine stripes
tri_period = 64
uu = np.mod(u, tri_period) - tri_period / 2
tri = ((bd < -150) & (bd > -150 - 52 + np.abs(uu) * 1.6)).astype(np.float32)
stripes = (((bd > 168) & (bd < 178)) | ((bd > 192) & (bd < 197)) | ((bd < -214) & (bd > -222))).astype(np.float32)
# inner motif: small diamonds rows inside band
dm = (np.abs(np.mod(u, 48) - 24) + np.abs(np.mod(bd + 150, 60) - 30)) < 13
inner_motif = (dm & (bd > -110) & (bd < 110)).astype(np.float32)
zari = np.clip(band + tri + stripes, 0, 1)
zari = ndi.gaussian_filter(zari, 0.9)
inner_motif = ndi.gaussian_filter(inner_motif, 0.9)

micro = (weave - .5) * 0.15 + slub * 0.5
height = hf * 26 + micro * 1.0 + zari * 1.5 + inner_motif * .8
n = normals(height, 1.0)

L = np.array([-0.85, -0.35, 0.42]); L /= np.linalg.norm(L)
V = np.array([0, 0, 1.0])
Hh = (L + V); Hh /= np.linalg.norm(Hh)
diff = np.clip(((n * L).sum(2) + 0.35) / 1.35, 0, 1) ** 1.1
ndh = np.clip((n * Hh).sum(2), 0, 1)
spec_silk = ndh ** 14
spec_zari = ndh ** 22

ivory = hexc('#f4ecdc'); shadow = hexc('#9a8569')
gold = hexc('#d2aa5c'); gold_dk = hexc('#4a3210'); gold_hi = hexc('#fff1c8')
base = shadow[None, None] * (1 - diff[..., None]) + ivory[None, None] * diff[..., None]
base = base * (0.96 + 0.06 * weave[..., None]) + slub[..., None] * 0.05
img = base + spec_silk[..., None] * 0.38 * hexc('#fff8ea')
zc = gold_dk * (1 - diff[..., None]) + gold * diff[..., None] + spec_zari[..., None] * 1.25 * gold_hi
zc = zc * (0.85 + 0.3 * weave[..., None])
zm = np.clip(zari - inner_motif * 0.75, 0, 1)[..., None]
img = img * (1 - zm) + zc * zm
# inner motif in ivory silk thread within zari
im = inner_motif[..., None] * band[..., None]
img = img * (1 - im) + (base * 1.02 + spec_silk[..., None] * .2) * im

# global raking falloff: light from top-left
fall = np.clip(1.05 - (x / W * 0.25 + y / H * 0.35), 0.55, 1.05)
img *= fall[..., None]
img = vignette(img, .22)
img = grain(img, .014)
save(img, 'plate-silk')
