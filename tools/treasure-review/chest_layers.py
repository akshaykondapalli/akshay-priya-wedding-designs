"""Split the approved Discovery artwork into layers for a real chest-opening interaction.
- discovery-base: original artwork with ONLY the lid area replaced by light spilling from the opened chest
- lid-front: exact pixels of the painted lid (incl. upper hasp), transparent elsewhere
- lid-under: generated underside of the lid (dark wood + brass trim), shown once the lid passes 90deg
- lock: exact pixels of the keyhole plate, for the lock jiggle
Everything outside the lid region is untouched."""
import numpy as np, cv2, json
from PIL import Image, ImageFilter
SRC='/home/claude/src-treasure/treasure_wedding_review/assets/01-discovery.png'
im=np.asarray(Image.open(SRC).convert('RGB')); H,W,_=im.shape
poly=np.array([(266,1263),(263,1215),(270,1180),(282,1150),(300,1130),(325,1117),(360,1112),(420,1110),(495,1107),(570,1111),(630,1116),(665,1125),(688,1145),(702,1170),(712,1205),(717,1263)],np.int32)
X0,Y0,X1,Y1=255,1098,725,1266
m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[poly],255)
lum=im.astype(float)@[0.299,0.587,0.114]
edge=cv2.dilate(255-m,np.ones((13,13),np.uint8))&m  # band just inside the outline
m[(edge>0)&(lum>205)]=0
alpha=cv2.GaussianBlur(m,(0,0),0.8)
lid=np.dstack([im,alpha])[Y0:Y1,X0:X1]
Image.fromarray(lid,'RGBA').save('lid-front.png')
# underside: dark wood planks lit warmly from inside the chest
h,w=Y1-Y0,X1-X0
yy,xx=np.mgrid[0:h,0:w].astype(float)
rng=np.random.default_rng(4)
grain=cv2.GaussianBlur(rng.random((h,w)).astype(np.float32),(0,0),sigmaX=18,sigmaY=1.2)
grain=(grain-grain.mean())/grain.std()
base=np.array([74,44,26.])+grain[...,None]*np.array([10,7,4.])
planks=(np.abs(((yy/h)*5)%1-0.5)<0.012)
base[planks]*=0.55
glow=np.exp(-((xx-w/2)/(w*0.42))**2)*np.clip(yy/h,0,1)**1.5
base=base*(1+glow[...,None]*0.9)+np.array([255,190,90.])*glow[...,None]*0.22
trim=(yy<7)|(yy>h-9)|(xx<10)|(xx>w-11)
base[trim]=np.array([176,132,62.])*(0.85+0.15*np.sin(xx[trim]/5))[...,None]
und=np.dstack([np.clip(base,0,255).astype(np.uint8),alpha[Y0:Y1,X0:X1]])
Image.fromarray(und,'RGBA').save('lid-under.png')
# base: replace lid area by reflecting the surrounding light rays radially (rays radiate from the chest),
# then add warm light rising from the opening
cx,cy=490,1268
src=im.astype(np.float32)
Y,Xg=np.mgrid[0:H,0:W].astype(np.float32)
ang=np.arctan2(Y-cy,Xg-cx); dist=np.hypot(Xg-cx,Y-cy)
pm=cv2.dilate(cv2.fillPoly(np.zeros((H,W),np.uint8),[poly],255),np.ones((7,7),np.uint8))
# boundary radius per angle bin
bins=720; Rb=np.zeros(bins)
ys,xs=np.nonzero(pm)
a_=np.arctan2(ys-cy,xs-cx); d_=np.hypot(xs-cx,ys-cy)
bi=((a_+np.pi)/(2*np.pi)*bins).astype(int)%bins
np.maximum.at(Rb,bi,d_)
Rb=np.maximum(Rb,1)
Rb=np.convolve(np.r_[Rb[-6:],Rb,Rb[:6]],np.ones(13)/13,'valid')
B=Rb[(((ang+np.pi)/(2*np.pi)*bins).astype(int))%bins]
rs=B+5+(B-dist)*0.55
mapx=(cx+np.cos(ang)*rs).astype(np.float32); mapy=(cy+np.sin(ang)*rs).astype(np.float32)
refl=cv2.remap(src,mapx,mapy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
refl=cv2.GaussianBlur(refl,(0,0),1.2)
core=np.exp(-((Xg-cx)/170)**2-((Y-cy)/70)**2)[...,None]
refl=refl*(1-core*0.55)+np.array([255,236,190.],np.float32)*core*0.55
fm=cv2.GaussianBlur(pm,(0,0),2.5).astype(np.float32)[...,None]/255
out=src*(1-fm)+refl*fm
# the chest interior, seen from the front once the lid swings up (box opening is a trapezoid:
# back rim at y=1150, front rim at the body edge). Hinge of the lid sits on the back rim.
BACK=1150; FRONT=1266
trap=np.array([(298,BACK),(684,BACK),(716,FRONT),(266,FRONT)],np.int32)
inner_mask=cv2.fillPoly(np.zeros((H,W),np.uint8),[trap],255)
rngi=np.random.default_rng(9)
gr=cv2.GaussianBlur(rngi.random((H,W)).astype(np.float32),(0,0),sigmaX=1.3,sigmaY=16); gr=(gr-gr.mean())/(gr.std()+1e-6)
wood=np.array([64,35,17.],np.float32)+gr[...,None]*np.array([10,6,3.],np.float32)
planks=(np.abs(((Xg-298)/38)%1-0.5)>0.47)[...,None]
wood=np.where(planks,wood*0.6,wood)
v=np.clip((Y-BACK)/(FRONT-BACK),0,1)[...,None]
interior=wood.copy()
# floor of the chest (lower part) catches the treasure light
floor=np.clip((Y-1192)/30,0,1)[...,None]
interior=interior*(1-floor)+np.array([150,92,38.],np.float32)*floor
core=np.exp(-((Xg-491)/150)**2-((Y-1236)/30)**2)[...,None]
interior=interior*(1-core)+np.array([255,244,205.],np.float32)*core
halo=np.exp(-((Xg-491)/230)**2-((Y-1232)/70)**2)[...,None]*0.75
interior=interior*(1-halo)+np.array([255,190,80.],np.float32)*halo
# side walls darker
lx=np.abs(Xg-491)
edge=np.clip((lx-(193+(Y-BACK)*0.27))/-30,0,1)[...,None]
interior=interior*(0.55+0.45*edge)
# brass trim along the back rim
trim=np.exp(-((Y-(BACK+3))/2.5)**2)[...,None]
interior=interior*(1-trim*0.85)+np.array([206,160,80.],np.float32)*trim*0.85
im_f=cv2.GaussianBlur(inner_mask,(0,0),0.9).astype(np.float32)[...,None]/255
out=out*(1-im_f)+interior*im_f
Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save('discovery-base.png')
# lock plate (body part of the latch) — exact pixels
LX0,LY0,LX1,LY1=436,1258,542,1322
lm=np.zeros((H,W),np.uint8)
cv2.rectangle(lm,(442,1262),(536,1316),255,-1)
lm=cv2.GaussianBlur(lm,(0,0),1)
lock=np.dstack([im,lm])[LY0:LY1,LX0:LX1]
Image.fromarray(lock,'RGBA').save('lock.png')
json.dump({'lid':[X0,Y0,X1,Y1],'lock':[LX0,LY0,LX1,LY1],'opening':[cx,cy]},open('chest.json','w'))
print('ok')
