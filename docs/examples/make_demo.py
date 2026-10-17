# Generate a demo dungeon image + Foundry scene export with walls.
import json, math, random
from PIL import Image, ImageDraw, ImageFilter
random.seed(3)
G = 100; W, H = 2000, 1400          # Foundry scene size (grid 100)
rooms = [(1,1,6,5,"Hall"),(8,1,12,4,"Library"),(14,1,19,6,"Shrine"),(1,7,5,13,"Barracks"),(7,6,12,13,"Great Room"),(14,8,19,13,"Vault")]
img = Image.new("RGB",(W,H),(40,46,40)); d = ImageDraw.Draw(img)
for x in range(0,W,7):
    for y in range(0,H,7):
        if random.random()<.05: d.point((x,y),(60,66,58))
cols=[(150,128,96),(120,110,140),(160,140,100),(130,120,100),(170,150,110),(110,120,130)]
for (x1,y1,x2,y2,_),c in zip(rooms,cols):
    d.rectangle([x1*G,y1*G,x2*G,y2*G],fill=c)
    for gx in range(x1,x2): 
        for gy in range(y1,y2): d.rectangle([gx*G+2,gy*G+2,gx*G+G-2,gy*G+G-2],outline=tuple(v-15 for v in c))
# corridors
cor=[(6,2,8,3),(12,2,14,3),(3,5,4,7),(9,4,10,6),(12,9,14,10),(5,9,7,10)]
for x1,y1,x2,y2 in cor: d.rectangle([x1*G,y1*G,x2*G,y2*G],fill=(120,110,95))
for (x1,y1,x2,y2,_) in rooms: d.rectangle([x1*G,y1*G,x2*G,y2*G],outline=(25,25,25),width=12)
for x1,y1,x2,y2 in cor:
    if x2-x1>y2-y1: d.line([x1*G,y1*G,x2*G,y1*G],fill=(25,25,25),width=12); d.line([x1*G,y2*G,x2*G,y2*G],fill=(25,25,25),width=12)
    else: d.line([x1*G,y1*G,x1*G,y2*G],fill=(25,25,25),width=12); d.line([x2*G,y1*G,x2*G,y2*G],fill=(25,25,25),width=12)
# The image is exported at 1.5x scene resolution to test scaling
img = img.resize((3000,2100)); img.save("./dungeon.png")

pad = 0.25; px = math.ceil(W*pad/G)*G; py = math.ceil(H*pad/G)*G
walls=[]
def wall(x1,y1,x2,y2,door=0): walls.append({"_id":str(len(walls)),"c":[x1*G+px,y1*G+py,x2*G+px,y2*G+py],"move":20,"sight":20,"light":20,"sound":20,"door":door,"ds":0})
def box_with_openings(x1,y1,x2,y2,openings):
    # openings: list of (side, a, b) in grid units along that side -> filled with doors
    sides={"t":((x1,y1),(x2,y1)),"b":((x1,y2),(x2,y2)),"l":((x1,y1),(x1,y2)),"r":((x2,y1),(x2,y2))}
    for s,((ax,ay),(bx,by)) in sides.items():
        cuts=sorted([(a,b) for (ss,a,b) in openings if ss==s])
        horiz = ay==by; start = ax if horiz else ay; end = bx if horiz else by; pos=start
        for a,b in cuts+[(end,end)]:
            if a>pos: wall(*( (pos,ay,a,ay) if horiz else (ax,pos,ax,a) ))
            if b>a: wall(*(((a,ay,b,ay) if horiz else (ax,a,ax,b))), door=1)
            pos=b
box_with_openings(1,1,6,5,[("r",2,3),("b",3,4)])
box_with_openings(8,1,12,4,[("l",2,3),("r",2,3),("b",9,10)])
box_with_openings(14,1,19,6,[("l",2,3)])
box_with_openings(1,7,5,13,[("t",3,4),("r",9,10)])
box_with_openings(7,6,12,13,[("t",9,10),("l",9,10),("r",9,10)])
box_with_openings(14,8,19,13,[("l",9,10)])
for x1,y1,x2,y2 in cor:
    if x2-x1>y2-y1: wall(x1,y1,x2,y1); wall(x1,y2,x2,y2)
    else: wall(x1,y1,x1,y2); wall(x2,y1,x2,y2)
scene={"name":"Demo Crypt","width":W,"height":H,"padding":pad,"grid":{"size":G,"type":1},"background":{"src":"dungeon.png","offsetX":0,"offsetY":0},"walls":walls}
json.dump(scene,open("./fvtt-Scene-demo-crypt.json","w"))
print(len(walls),"walls")
