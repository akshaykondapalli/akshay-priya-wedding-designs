import wc, numpy as np
from PIL import Image
from scipy import ndimage as ndi
wc.seed(3)
size = 640
h = wc.paper_height((size, size), wrap=True)
gy, gx = np.gradient(ndi.gaussian_filter(h, 1.0, mode='wrap'))
shade = np.clip(1 + 11 * (gx - gy), 0.78, 1.15)
col = wc.hexrgb('#f8f2e6')[None, None, :] * (0.955 + 0.05 * shade[..., None])
mott = wc.fbm((size, size), scales=(40, 90), wrap=True)
col *= (0.985 + 0.025 * mott[..., None])
Image.fromarray((np.clip(col, 0, 1) * 255).astype('uint8')).save('/home/claude/site/watercolor/img/paper.webp', quality=90, method=6)
