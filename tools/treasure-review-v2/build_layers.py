"""Build animation layers for The Treasure We Found from the approved high-resolution storyboard frames.
Only the pieces that must move are separated; everything else stays exactly as painted.
Frames: /home/claude/src-t2/hi/f1..f9.png (941x1672)."""
import numpy as np, cv2, json, os
from PIL import Image
S='/home/claude/src-t2/hi/'; O='/home/claude/site/treasure-review/img/'; os.makedirs(O,exist_ok=True)
L=lambda n: np.asarray(Image.open(S+n).convert('RGB'))
f1,f2,f3,f4,f5,f6,f7,f8,f9=[L(f'f{i}.png') for i in range(1,10)]
H,W=1672,941

def remove_pill(img,box,src_dy=95):
    """Remove the painted 'Music Coming Soon' pill by cloning parchment from just below it (Poisson blend)."""
    x0,y0,x1,y1=box
    patch=img[y0+src_dy:y1+src_dy,x0:x1].copy()
    return cv2.seamlessClone(patch[...,::-1].copy(),img[...,::-1].copy(),255*np.ones(patch.shape[:2],np.uint8),((x0+x1)//2,(y0+y1)//2),cv2.NORMAL_CLONE)[...,::-1]
Y,X=np.mgrid[0:H,0:W].astype(np.float32)
def save(a,n,q=88):
    im=Image.fromarray(a); im.save(O+n,quality=q,method=6); return n
meta={}

# ---------- Scene 1 ----------
save(f1,'s1-cover.webp',90)
save(f3,'s1-open.webp',90)
# lid of the closed chest (frame 2): dome down to the seam at y=1193, incl. upper half of the hasp
lid_poly=np.array([(132,1194),(131,1060),(140,1010),(168,975),(225,952),(320,944),(470,940),(620,944),(715,952),(772,975),(800,1010),(812,1060),(813,1194)],np.int32)
lm=np.zeros((H,W),np.uint8); cv2.fillPoly(lm,[lid_poly],255)
lab=cv2.cvtColor(f2,cv2.COLOR_RGB2HSV).astype(int)
# remove the bright glowing background that sits inside the rough outline near the dome edge
edge=cv2.dilate(255-lm,np.ones((15,15),np.uint8))&lm
bright=(lab[...,2]>235)&(lab[...,1]<120)
lm[(edge>0)&bright]=0
lm=cv2.GaussianBlur(lm,(0,0),0.9)
LX0,LY0,LX1,LY1=120,930,826,1198
save(np.dstack([f2,lm])[LY0:LY1,LX0:LX1],'s1-lid.webp',92)
# chest interior shown when the lid lifts: an opening full of warm light (as in frame 3), brass back rim, soft walls
BACK=1060; FRONT=1196
base2=f2.astype(np.float32).copy()
ld=cv2.fillPoly(np.zeros((H,W),np.uint8),[lid_poly],255)
soft=cv2.GaussianBlur(cv2.dilate(ld,np.ones((25,25),np.uint8)),(0,0),16).astype(np.float32)[...,None]/255
r=np.hypot((X-472)/430,(Y-1150)/260)[...,None]
lightfield=np.array([255,250,232.],np.float32)*np.clip(1-r,0,1)**0.6+np.array([250,206,120.],np.float32)*(1-np.clip(1-r,0,1)**0.6)
base2=base2*(1-soft)+lightfield*soft
trap=np.array([(178,BACK),(766,BACK),(812,FRONT),(132,FRONT)],np.int32)
tm=cv2.GaussianBlur(cv2.fillPoly(np.zeros((H,W),np.uint8),[trap],255),(0,0),1.2).astype(np.float32)[...,None]/255
lx=np.abs(X-472); wall=np.clip((lx-(250+(Y-BACK)*0.33))/40,0,1)[...,None]
inner=np.array([255,244,205.],np.float32)*(1-wall)+np.array([150,86,34.],np.float32)*wall
depth=np.clip((Y-BACK)/(FRONT-BACK),0,1)[...,None]
inner=inner*(0.86+0.14*depth)
rim=np.exp(-((Y-(BACK+2))/3.0)**2)[...,None]*(np.abs(X-472)<300)[...,None]
inner=inner*(1-rim*0.9)+np.array([170,118,52.],np.float32)*rim*0.9
base2=base2*(1-tm)+inner*tm
save(np.clip(base2,0,255).astype(np.uint8),'s1-chest-base.webp',90)
# lock plate (lower half of the hasp, on the body) for the unlock jiggle — exact pixels
KX0,KY0,KX1,KY1=420,1188,526,1252
km=np.zeros((H,W),np.uint8); cv2.rectangle(km,(426,1194),(520,1246),255,-1); km=cv2.GaussianBlur(km,(0,0),1)
save(np.dstack([f2,km])[KY0:KY1,KX0:KX1],'s1-lock.webp',92)
# light-free version of frame 2 is the closed chest exactly as painted (for the no-JS / first state)
save(f2,'s1-chest.webp',90)
meta['lid']=[LX0,LY0,LX1,LY1]; meta['lock']=[KX0,KY0,KX1,KY1]

# ---------- Scene 2: clean map (frame 4) with the painted button removed ----------
patch=f4[1150:1300,105:330].copy()          # clean parchment from the same frame
row=np.concatenate([patch,patch[:,::-1]],1); tile=np.concatenate([row,row[::-1]],0)
reg_w,reg_h=774-158,1554-1418
big=np.tile(tile,(2,3,1))[:reg_h+20,:reg_w+20]
inp=cv2.seamlessClone(big[...,::-1].copy(),f4[...,::-1].copy(),255*np.ones(big.shape[:2],np.uint8),((158+774)//2,(1418+1554)//2),cv2.NORMAL_CLONE)[...,::-1]
save(inp.astype(np.uint8),'s2-map.webp',90)

# routes: traced from frame 6, re-anchored onto frame 4's own pins with a per-route similarity transform
R1=[(143,690),(153,717),(162,729),(177,740),(196,748),(216,753),(237,757),(256,761),(274,767),(294,774),(311,783),(328,793),(344,804),(360,816),(375,827),(390,839),(406,853),(422,868),(441,885),(457,903),(472,919),(486,936),(496,949),(508,965),(521,986),(534,1007),(545,1027),(556,1048),(566,1070),(575,1090),(583,1109),(600,1128)]
R2=[(528,712),(546,755),(561,774),(574,792),(585,811),(595,830),(603,851),(611,872),(617,895),(622,918),(624,940),(626,962),(626,985),(625,1009),(622,1032),(620,1056),(617,1078),(614,1101),(611,1124)]
TOR=(141,668); GER=(565,708); DEST=(612,1112)   # f4 pin tips and destination (palace shore)
def sim(pts,a2,b2):
    P=np.array(pts,float); a1,b1=P[0],P[-1]
    v1=b1-a1; v2=np.array(b2,float)-np.array(a2,float)
    s=np.linalg.norm(v2)/np.linalg.norm(v1); ang=np.arctan2(v2[1],v2[0])-np.arctan2(v1[1],v1[0])
    Rm=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])*s
    return ((P-a1)@Rm.T+np.array(a2)).round(1).tolist()
r1=sim(R1,TOR,DEST); r2=sim(R2,GER,DEST)
def bez(P):
    P=[P[0]]+P+[P[-1]]; d=f"M{P[1][0]:.1f} {P[1][1]:.1f}"
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=map(np.array,(P[i-1],P[i],P[i+1],P[i+2]))
        c1=p1+(p2-p0)/6; c2=p2-(p3-p1)/6
        d+=f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d
# thin to every 2nd point for a smoother curve
r1s=r1[::2]+([r1[-1]] if len(r1)%2==0 else []); r2s=r2[::2]+([r2[-1]] if len(r2)%2==0 else [])
meta['routes']={'toronto':bez(r1s),'germany':bez(r2s),'dest':DEST,'tor':TOR,'ger':GER}

# ---------- Scene 3: invitation (frame 7) with the couple's real photo in the polaroid ----------
photo=np.asarray(Image.open('/home/claude/src-t2/photos/couple-clean.png').convert('RGB'))
crop=photo[0:960,0:1470]
Q=np.float32([(57,104),(846,22),(896,527),(116,602)])
Mw=cv2.getPerspectiveTransform(np.float32([(0,0),(1470,0),(1470,960),(0,960)]),Q)
warp=cv2.warpPerspective(crop,Mw,(W,H),flags=cv2.INTER_LANCZOS4)
qm=np.zeros((H,W),np.uint8); cv2.fillPoly(qm,[Q.astype(np.int32)],255)
# keep the painted foreground that overlaps the photo: wax seal + ribbon + the flower spray above it
fg=np.zeros((H,W),np.uint8)
cv2.circle(fg,(786,527),108,255,-1)
cv2.fillPoly(fg,[np.array([(735,470),(752,395),(800,372),(870,368),(912,395),(915,470),(860,470)],np.int32)],255)
fg=cv2.GaussianBlur(fg,(0,0),2.5)
a=(cv2.GaussianBlur(qm,(0,0),0.8).astype(np.float32)/255)*(1-fg.astype(np.float32)/255)
# gentle warm grade so the photo sits in the scene's light
w=warp.astype(np.float32); w=w*np.array([1.03,1.0,0.94])+np.array([6,3,0.])
inv=f7.astype(np.float32)*(1-a[...,None])+np.clip(w,0,255)*a[...,None]
save(inv.astype(np.uint8),'s3-invite.webp',90)
json.dump(meta,open('/home/claude/tools-t2/meta.json','w'),indent=1)
print('ok')
