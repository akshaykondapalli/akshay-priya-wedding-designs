import math, numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from common import *
OUT='/home/claude/site/heritage/img/'
S=640; c=S/2
y,x=np.mgrid[0:S,0:S].astype(np.float32)
ang=np.arctan2(y-c,x-c); r=np.hypot(x-c,y-c)
rim=230+18*np.sin(ang*5+1)+12*np.sin(ang*9)+noise(S,S,40,3)*26
blob=np.clip((rim-r)/6,0,1)
# dome height
hgt=np.clip(1-(r/rim)**2,0,1)**0.35*1.0
# pressed disc + ring + monogram
disc=np.clip((175-r)/3,0,1)
ring=np.clip(1-np.abs(r-160)/3,0,1)+np.clip(1-np.abs(r-150)/1.5,0,1)*0.6
def mono(d,s):
    f=font('csc',int(150*s)); f2=font('cgi',int(64*s))
    d.text((c*s-118*s,c*s-100*s),'A',font=f,fill=255)
    d.text((c*s+18*s,c*s-100*s),'P',font=f,fill=255)
    tw=d.textlength('&',font=f2); d.text((c*s-tw/2,c*s-40*s),'&',font=f2,fill=255)
    for i in range(24):
        a=i/24*2*math.pi; xx=c*s+math.cos(a)*130*s; yy=c*s+math.sin(a)*130*s
        d.ellipse([xx-3*s,yy-3*s,xx+3*s,yy+3*s],fill=255)
m=mask_from_draw(S,S,mono,2)
height=hgt*18 - disc*7 + ring*2.5 + ndi.gaussian_filter(m,1.0)*3.2 + noise(S,S,4,2)*0.4
n=normals(height,1.0)
L=(-0.5,-0.6,0.65)
dif=light(n,L); sp=spec(n,L,40)
base=hexc('#6d1418')
col=base*(0.25+0.95*dif[...,None])+sp[...,None]*hexc('#ffcf9a')*0.55
# gilded relief: gold on raised monogram & ring
g=np.clip(ndi.gaussian_filter(m,0.7)+ring*0.8,0,1)
gold=hexc('#7a5420')*(1-dif[...,None])+hexc('#e6c47a')*dif[...,None]+sp[...,None]*0.6
col=col*(1-g[...,None]*0.85)+gold*g[...,None]*0.85
# soft shadow
sh=ndi.gaussian_filter(np.roll(np.roll(blob,14,0),10,1),10)*0.6
outa=np.maximum(blob,sh)
col=col*blob[...,None]
im=save(col,OUT+'seal.webp',q=84,alpha=outa,size=(320,320))
