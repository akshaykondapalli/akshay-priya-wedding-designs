"""Convert raw 390x844@2x captures into comparison thumbnails (WebP) and build a 1200x630 og.jpg.
Usage: python3 make-previews.py <raw_dir> <site_dir> <title> <slug,slug,...>"""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
raw, site, title, slugs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
out = os.path.join(site, 'previews'); os.makedirs(out, exist_ok=True)
for f in glob.glob(os.path.join(raw, '*.png')):
    im = Image.open(f).convert('RGB')
    im = im.resize((520, int(im.height * 520 / im.width)), Image.LANCZOS)
    im.save(os.path.join(out, os.path.basename(f)[:-4] + '.webp'), quality=80, method=6)
# og image: arrival screens side by side on the gallery wall
W, H = 1200, 630
og = Image.new('RGB', (W, H), (23, 21, 26))
n = len(slugs); gap = 22; ph = 520; pw = int(ph * 390 / 844)
total = n * pw + (n - 1) * gap; x0 = (W - total) // 2
for i, s in enumerate(slugs):
    p = os.path.join(raw, f'{s}-arrival.png')
    if not os.path.exists(p): continue
    im = Image.open(p).convert('RGB').resize((pw, ph), Image.LANCZOS)
    og.paste(im, (x0 + i * (pw + gap), 40))
d = ImageDraw.Draw(og)
try:
    fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 26)
except Exception:
    fnt = ImageFont.load_default()
d.text((W // 2, 595), title, fill=(227, 196, 143), font=fnt, anchor='mm')
og.save(os.path.join(out, 'og.jpg'), quality=82, optimize=True)
print('ok', len(glob.glob(os.path.join(out, '*.webp'))), 'thumbs')
