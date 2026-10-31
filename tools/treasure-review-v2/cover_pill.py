"""Cover ONLY the painted 'Music Coming Soon' pill in scene-1 frames with parchment texture from the same frame.
Texture: image quilting from a clean parchment area of that frame; tone: low-frequency colour from the surroundings.
Pixels outside the pill rectangle (plus a 6 px feather) are untouched. Writes *-final.webp next to the originals."""
import numpy as np, cv2, sys
from PIL import Image
D = '/home/claude/site/treasure-review/img/'
rng = np.random.default_rng(7)
def quilt(pool, h, w, B=36, O=10):
    ph, pw = pool.shape[:2]; out = np.zeros((h + B, w + B, 3), np.float32)
    step = B - O
    for y in range(0, h, step):
        for x in range(0, w, step):
            cands = []
            for _ in range(160):
                py, px = rng.integers(0, ph - B), rng.integers(0, pw - B)
                blk = pool[py:py + B, px:px + B]
                e = 0
                if x > 0: e += ((blk[:, :O] - out[y:y + B, x:x + O]) ** 2).sum()
                if y > 0: e += ((blk[:O, :] - out[y:y + O, x:x + B]) ** 2).sum()
                cands.append((e, py, px))
            cands.sort(key=lambda c: c[0]); e, py, px = cands[rng.integers(0, 4)]
            blk = pool[py:py + B, px:px + B].copy()
            m = np.ones((B, B, 1), np.float32)
            if x > 0: m[:, :O] = np.linspace(0, 1, O)[None, :, None]
            if y > 0: m[:O, :] = np.minimum(m[:O, :], np.linspace(0, 1, O)[:, None, None])
            out[y:y + B, x:x + B] = out[y:y + B, x:x + B] * (1 - m) + blk * m
    return out[:h, :w]
def cover(name, rect, poolrect):
    im = np.asarray(Image.open(D + name + '.webp').convert('RGB')).astype(np.float32)
    x0, y0, x1, y1 = rect; px0, py0, px1, py1 = poolrect
    pool = im[py0:py1, px0:px1]
    tex = quilt(pool, y1 - y0 + 24, x1 - x0 + 24)
    H, W = im.shape[:2]
    m = np.zeros((H, W), np.float32); m[y0:y1, x0:x1] = 1
    known = 1 - cv2.dilate(m, np.ones((25, 25), np.uint8))
    hsv = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    parch = ((hsv[..., 0] >= 6) & (hsv[..., 0] <= 28) & (hsv[..., 2] > 150) & (hsv[..., 1] < 175)).astype(np.float32)
    known = known * cv2.erode(parch, np.ones((5, 5), np.uint8))
    low = cv2.GaussianBlur(im * known[..., None], (0, 0), 22) / (cv2.GaussianBlur(known, (0, 0), 22)[..., None] + 1e-6)
    full = np.zeros_like(im); full[y0 - 12:y1 + 12, x0 - 12:x1 + 12] = tex
    tl = cv2.GaussianBlur(full, (0, 0), 22); tm = np.zeros((H, W), np.float32); tm[y0 - 12:y1 + 12, x0 - 12:x1 + 12] = 1
    tl = tl / (cv2.GaussianBlur(tm, (0, 0), 22)[..., None] + 1e-6)
    fill = (full - tl) * 0.55 + low
    a = cv2.GaussianBlur(cv2.dilate(m, np.ones((7, 7), np.uint8)), (0, 0), 5)[..., None]
    a[:y0 - 12] = 0; a[y1 + 12:] = 0; a[:, :x0 - 12] = 0; a[:, x1 + 12:] = 0
    out = np.clip(im * (1 - a) + fill * a, 0, 255).astype(np.uint8)
    # export ONLY the patch (with its soft alpha edge) as an overlay; the original artwork file is left untouched
    X0, Y0, X1, Y1 = x0 - 14, y0 - 14, x1 + 14, y1 + 14
    patch = np.dstack([out[Y0:Y1, X0:X1], (a[Y0:Y1, X0:X1, 0] * 255).round().astype(np.uint8)])
    Image.fromarray(patch, 'RGBA').save(D + name + '-labelpatch.webp', quality=92, method=6)
    print(name, 'patch at', X0, Y0, X1 - X0, Y1 - Y0)
    return out
c = cover('s1-cover', (478, 42, 924, 148), (600, 170, 935, 330))
h = cover('s1-chest', (476, 49, 924, 156), (610, 165, 935, 270))
o = cover('s1-open', (474, 36, 928, 145), (610, 150, 935, 240))
prev = np.concatenate([x[0:300, 300:941] for x in (c, h, o)], 0)
Image.fromarray(prev).save('/tmp/claude-0/-home-claude/2cf5e8b2-6ab2-523a-8d34-c01756c66623/scratchpad/cover.jpg', quality=88)
print('ok')
