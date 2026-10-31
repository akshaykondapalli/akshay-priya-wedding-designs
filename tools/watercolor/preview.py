import sys, numpy as np
from PIL import Image
import wc
wc.seed(3)
tile = wc.paper_tile(768)
Image.fromarray((tile*255).astype('uint8')).save('/home/claude/qa/watercolor/paper_tile.png')
for f in sys.argv[1:]:
    im = np.asarray(Image.open(f).convert('RGB'), np.float32)/255
    h,w,_=im.shape
    t = np.tile(tile, (h//768+1, w//768+1, 1))[:h,:w]
    out = im*t
    Image.fromarray((out*255).astype('uint8')).resize((w//2,h//2), Image.LANCZOS).save(f.replace('.png','_prev.jpg').replace('.webp','_prev.jpg'), quality=88)
