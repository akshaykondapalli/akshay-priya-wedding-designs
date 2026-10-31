"""Clean the Journey artwork: remove baked aircraft and the dashed route cores along a fitted corridor.
Leaves the soft glow, pins, landmarks, text and all other artwork untouched."""
import numpy as np, cv2, json
from PIL import Image
SRC='/home/claude/src-treasure/treasure_wedding_review/assets/02-journey.png'
im=np.asarray(Image.open(SRC).convert('RGB')); H,W,_=im.shape
R=json.load(open('routes.json'))
def catmull(pts,steps=20):
    P=np.array(pts,float); P=np.vstack([P[0],P,P[-1]]); out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
        for t in np.linspace(0,1,steps,endpoint=False):
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    out.append(P[-2]); return np.array(out)
r1=[R['toronto']]+R['R1']+[R['heart']]
r2=[R['germany']]+R['R2']+[R['heart']]
mask=np.zeros((H,W),np.uint8)
for pts in (r1,r2):
    c=catmull(pts).round().astype(np.int32)
    cv2.polylines(mask,[c.reshape(-1,1,2)],False,1,thickness=13)
# protect pins (keep painted pins intact)
for (x,y),rad in ((R['toronto'],17),(R['germany'],17),(R['heart'],24)):
    cv2.circle(mask,(x,y),rad,0,-1)
a=im.astype(int); rr,gg,bb=a[...,0],a[...,1],a[...,2]
dash=((rr>120)&(gg>65)&(gg<160)&(bb<90)&(rr-bb>80)).astype(np.uint8)
for (x,y,w,h) in [(296,660,54,50),(445,822,51,43)]:
    sub=np.zeros_like(mask); sub[y-5:y+h+5,x-5:x+w+5]=dash[y-5:y+h+5,x-5:x+w+5]
    mask|=cv2.dilate(sub,np.ones((7,7),np.uint8))
out=cv2.inpaint(im[...,::-1].copy(),mask*255,7,cv2.INPAINT_TELEA)[...,::-1]
# soften the inpainted corridor a touch so no streaks remain
blur=cv2.GaussianBlur(out,(0,0),2.2)
m=cv2.GaussianBlur(mask.astype(np.float32),(0,0),2)[...,None]
out=(out*(1-m)+blur*m).astype(np.uint8)
Image.fromarray(out).save('journey-clean.png')
json.dump({'r1':catmull(r1,8).round(1).tolist(),'r2':catmull(r2,8).round(1).tolist(),'r1pts':r1,'r2pts':r2},open('route-paths.json','w'))
print('ok')
