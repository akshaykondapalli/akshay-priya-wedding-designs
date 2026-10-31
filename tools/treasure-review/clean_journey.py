"""Remove the baked-in aircraft and dashed routes from the approved Journey artwork so they can be
re-created as live SVG layers. Pins, landmarks, text and everything else are left untouched."""
import numpy as np, cv2, json
from PIL import Image
SRC='/home/claude/src-treasure/treasure_wedding_review/assets/02-journey.png'
im=np.asarray(Image.open(SRC).convert('RGB'))
a=im.astype(int); r,g,b=a[...,0],a[...,1],a[...,2]
dash=((r>130)&(r<215)&(g>75)&(g<150)&(b<70)&(r-b>100)).astype(np.uint8)
n,lab,st,cen=cv2.connectedComponentsWithStats(dash,8)
R1=[(197,668),(210,679),(226,686),(241,688),(256,687),(272,685),(287,683),(357,697),(374,708),(384,717),(393,727),(400,739),(406,753),(411,768),(417,783),(423,797),(430,811),(440,824),(500,877),(513,887),(527,896),(542,902),(558,908),(574,912),(590,917),(605,921),(620,926),(634,931),(647,938),(658,947),(668,956),(676,967)]
R2=[(546,706),(550,723),(559,737),(570,747),(583,755),(596,763),(610,770),(622,776),(643,791),(655,801),(665,812),(675,825),(683,839),(690,853),(695,868),(699,885),(702,903),(702,920),(702,937),(701,953)]
planes=[(296,660,54,50),(445,822,51,43)]
mask=np.zeros(dash.shape,np.uint8)
for (x,y) in R1+R2:
    i=lab[y,x] if lab[y,x] else None
    if i is None:
        # nearest component
        ys,xs=np.nonzero(lab[y-6:y+7,x-6:x+7]); 
        if len(ys): i=lab[y-6+ys[0],x-6+xs[0]]
    if i: mask[lab==i]=1
for (x,y,w,h) in planes:
    sub=lab[y:y+h,x:x+w]; ids=np.unique(sub[sub>0])
    for i in ids:
        if st[i][4]>300: mask[lab==i]=1
# dashes between first/last listed (e.g. near pins) also covered: the strokes 683-700 near heart
mask=cv2.dilate(mask,np.ones((5,5),np.uint8),iterations=1)
# extra halo around planes (dark outline/shadow)
for (x,y,w,h) in planes:
    sub=mask[y-4:y+h+4,x-4:x+w+4]; mask[y-4:y+h+4,x-4:x+w+4]=cv2.dilate(sub,np.ones((5,5),np.uint8),iterations=1)
out=cv2.inpaint(im[...,::-1].copy(),mask*255,6,cv2.INPAINT_TELEA)[...,::-1]
Image.fromarray(out).save('/home/claude/tools-treasure/journey-clean.png')
Image.fromarray(mask*255).save('/home/claude/tools-treasure/journey-mask.png')
json.dump({'R1':R1,'R2':R2,'toronto':[182,636],'germany':[554,682],'heart':[692,1012]},open('/home/claude/tools-treasure/routes.json','w'))
print('masked px',int(mask.sum()))
