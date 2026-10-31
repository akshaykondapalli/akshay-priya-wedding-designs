import math, numpy as np
from scipy import ndimage as ndi
from PIL import Image
from garland import bud, blossom
OUT='/home/claude/site/heritage/img/'
rng=np.random.default_rng(14)
W,H=900,220
c=Image.new('RGBA',(W,H),(0,0,0,0))
items=[]
# loose buds lying flat at random angles, denser toward the centre (under the lamps)
for i in range(18):
    x=rng.normal(450,210); y=rng.uniform(60,170)
    items.append(('b',x,y,rng.uniform(0,360),rng.uniform(.9,1.15),i))
for i in range(8):
    x=rng.normal(450,230); y=rng.uniform(70,160)
    items.append(('f',x,y,rng.uniform(0,360),rng.uniform(.85,1.1),i))
# single fallen petals
for i in range(7):
    x=rng.normal(450,250); y=rng.uniform(80,180)
    items.append(('p',x,y,rng.uniform(0,360),rng.uniform(.8,1),i))
rng.shuffle(items)
for k,x,y,a,s,i in items:
    if k=='b': im=bud(54,15,tint=rng.random(),seed=i)
    elif k=='f': im=blossom(30,seed=i)
    else: im=bud(22,12,tint=.2,seed=i+40)
    im=im.resize((max(4,int(im.width*s)),max(4,int(im.height*s))),Image.LANCZOS).rotate(a,resample=Image.BICUBIC,expand=True)
    x=min(max(x,30),W-30)
    c.alpha_composite(im,(int(x-im.width/2),int(y-im.height/2)))
A=np.asarray(c)[...,3].astype(np.float32)/255
sh=ndi.gaussian_filter(np.roll(np.roll(A,7,0),5,1),5)*.6
base=np.zeros((H,W,4),np.uint8); base[...,:3]=(18,8,4); base[...,3]=(np.clip(sh,0,1)*255).astype(np.uint8)
out=Image.fromarray(base,'RGBA'); out.alpha_composite(c)
out.save(OUT+'jasmine-scatter.webp','WEBP',quality=82,method=6)
s=Image.new('RGBA',(W,H),(34,18,10,255)); s.alpha_composite(out); s.save('/home/claude/qa/heritage/scatter-check.png')
