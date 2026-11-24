"""Generate deterministic original WWII ambience; never burn fake UI status into art."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import random, math
OUT=Path(__file__).resolve().parents[1]/"assets"/"ui_wwii"
OUT.mkdir(parents=True,exist_ok=True)
def texture(w,h,base,seed,grain=11):
    rng=random.Random(seed)
    im=Image.new("RGB",(w,h)); px=im.load()
    for y in range(h):
        for x in range(w):
            n=rng.gauss(0,grain)+math.sin(x*.016+y*.034)*3
            px[x,y]=tuple(max(0,min(255,int(v+n))) for v in base)
    return im
plate=texture(1024,52,(55,48,35),197,16); d=ImageDraw.Draw(plate,"RGBA")
for y in (0,1,3,47,49,50):d.line((0,y,1024,y),fill=(216,167,101,110))
for x in (17,1007):
    d.ellipse((x-5,11,x+5,21),fill=(7,7,6,195),outline=(194,158,103,178))
    d.line((x-3,16,x+3,16),fill=(164,121,73,180),width=1)
for i in range(150):
    rng=random.Random(i+86)
    x=rng.randrange(1024); y=rng.randrange(52)
    d.line((x,y,x+rng.randrange(5,80),y),fill=(8,6,4,rng.randint(8,28)))
plate.save(OUT/"plate.png",optimize=True)
panel=texture(1024,350,(28,26,20),130,9);d=ImageDraw.Draw(panel,"RGBA")
for i in range(1600):
    rng=random.Random(i+240)
    x=rng.randrange(1024);y=rng.randrange(350);r=rng.randrange(4,60)
    d.line((x,y,x+r,y),fill=(120,88,49,rng.randint(3,16)))
panel.save(OUT/"panel.png",optimize=True)
W,H=1500,166
im=Image.new("RGB",(W,H)); px=im.load();rng=random.Random(57)
for y in range(H):
    for x in range(W):
        cloud=math.sin(x*.025+y*.022)*9+math.sin(x*.057-y*.014)*5
        shadow=.40+.60*min(1,max(0,(x-330)/400))
        px[x,y]=tuple(int(max(3,min(255,(c+cloud+rng.randint(-8,8))*shadow)))
                       for c in (103-72*y/H,86-63*y/H,63-53*y/H))
d=ImageDraw.Draw(im,"RGBA")
# Ruined town silhouettes behind the cinematic brand header.
for x,w,h in ((530,86,60),(642,106,80),(778,92,69),(902,102,89),(1032,100,63),(1160,111,87),(1338,120,72)):
    y=H-h
    d.rectangle((x,y,x+w,H),fill=(31,29,23,233))
    d.polygon([(x-5,y+10),(x+w//3,y-16),(x+w+4,y+11)],fill=(22,22,18,241))
    for xx in range(x+11,x+w-8,25):
        for yy in range(y+20,H-18,33):
            d.rectangle((xx,yy,xx+10,yy+15),fill=(7,11,10,224))
    rr=random.Random(x)
    for _ in range(15):
        xx=x+rr.randrange(w);yy=y+rr.randrange(max(1,h//2))
        d.rectangle((xx,yy,xx+rr.randrange(3,11),yy+3),fill=(147,125,89,36))
d.rectangle((937,31,968,120),fill=(34,32,25,255))
d.polygon([(932,32),(952,3),(976,32)],fill=(26,24,19,255))
d.rectangle((944,53,956,72),fill=(5,8,8,230))
# Leafless tree and battleground debris
for a,b in [((1320,160),(1319,30)),((1320,65),(1273,10)),((1320,88),(1388,12)),((1315,105),(1251,59)),((1320,55),(1350,0))]:
    d.line((*a,*b),fill=(12,14,11,238),width=4 if a[1]>90 else 2)
d.rectangle((0,H-15,W,H),fill=(20,19,15,221))
for i in range(260):
    xx=rng.randrange(400,W);yy=rng.randrange(124,H)
    d.ellipse((xx,yy,xx+rng.randrange(2,14),yy+rng.randrange(1,4)),fill=(190,150,95,rng.randrange(10,50)))
# Armoured truck silhouette
d.rectangle((1118,115,1202,140),fill=(23,25,20,255))
d.polygon([(1130,108),(1178,108),(1194,128),(1130,128)],fill=(36,38,29,255))
for xx in (1135,1191): d.ellipse((xx-10,133,xx+10,153),fill=(8,10,9,255),outline=(111,93,67,130))
# Decorative WWII helmet silhouette left
d.ellipse((-82,-85,190,118),fill=(15,15,12,252),outline=(140,117,74,180),width=3)
d.polygon([(0,69),(183,61),(223,95),(0,117)],fill=(12,12,11,250))
for t in range(-140,170,22):
    d.line((t,-20,t+141,110),fill=(139,125,80,80),width=2)
    d.line((t,108,t+140,-20),fill=(139,125,80,65),width=2)
# Documentary U.S. Army photo (public domain) blends real WWII ruined
# architecture into the user's approved military moodboard. The photograph
# is entirely background art. It is NOT a CoD2 screenshot or live server.
photo_file=OUT/"source_coutances.jpg"
if photo_file.exists():
    historic=Image.open(photo_file).convert("RGB")
    # Long street strip: buildings + tanks, avoiding fake text/status.
    crop=historic.crop((35,175,955,665))
    crop=crop.resize((990,320),Image.Resampling.LANCZOS)
    # Sepia metallic tone consistent with the reference painting.
    sepia=Image.new("RGB",crop.size)
    sp=sepia.load();ip=crop.load()
    for yy in range(crop.height):
        for xx in range(crop.width):
            red,green,blue=ip[xx,yy]
            lum=int(red*.30+green*.59+blue*.11)
            sp[xx,yy]=(min(255,int(lum*.92)+17),min(255,int(lum*.78)+13),
                        min(255,int(lum*.52)+10))
    crop=Image.blend(crop,sepia,.72).crop((0,52,990,218))
    base=im.convert("RGBA")
    layer=Image.new("RGBA",(W,H),(0,0,0,0))
    mask=Image.new("L",(990,H),0)
    mp=mask.load()
    for yy in range(H):
        for xx in range(990):
            blend=min(1,max(0,(xx-20)/220))
            darken=min(1,max(0,(yy-2)/80))
            mp[xx,yy]=int(222*blend*(.55+.45*darken))
    layer.paste(crop,(510,0),mask)
    im=Image.alpha_composite(base,layer).convert("RGB")
    # Darken behind the actual brand so lettering remains fully legible.
    for xx in range(0,700):
        strength=max(0,(700-xx)/700)
        for yy in range(H):
            r,g,b=im.getpixel((xx,yy))
            ratio=1-strength*.40
            im.putpixel((xx,yy),(int(r*ratio),int(g*ratio),int(b*ratio)))
    server=historic.crop((195,172,895,645)).resize((255,120),Image.Resampling.LANCZOS)
    server=Image.blend(server,Image.new("RGB",server.size,(98,75,45)),.18)
    server.save(OUT/"server_scene.png",optimize=True)
else:
    im.crop((720,28,1190,154)).resize((255,120),Image.Resampling.LANCZOS).save(OUT/"server_scene.png",optimize=True)
im.save(OUT/"hero.png",optimize=True)
# Real small monochrome menu glyph images so Windows font fallback never
# displays an unknown-character square instead of a navigation icon.
for icon in ("home","knowledge","stats","settings","updates","discord","about"):
    glyph=Image.new("RGBA",(26,26),(0,0,0,0))
    g=ImageDraw.Draw(glyph)
    color=(230,187,116,255)
    if icon=="home":
        g.polygon([(3,12),(13,3),(23,12)],outline=color)
        g.rectangle((6,12,20,23),outline=color,width=2)
        g.rectangle((11,17,15,23),fill=color)
    elif icon=="knowledge":
        for y in (5,12,19):
            g.rectangle((4,y,22,y+5),outline=color,width=2)
    elif icon=="stats":
        for x,h in ((4,10),(11,17),(18,21)):
            g.rectangle((x,24-h,x+4,24),fill=color)
    elif icon=="settings":
        g.ellipse((4,4,22,22),outline=color,width=3)
        g.ellipse((10,10,16,16),outline=color,width=2)
        for a,b,c,d in ((13,0,13,5),(13,21,13,26),(0,13,5,13),(21,13,26,13)):
            g.line((a,b,c,d),fill=color,width=3)
    elif icon=="updates":
        g.line((13,2,13,20),fill=color,width=3)
        g.line((7,15,13,21,19,15),fill=color,width=3)
        g.line((4,24,22,24),fill=color,width=2)
    elif icon=="discord":
        g.rounded_rectangle((2,6,24,21),radius=6,outline=color,width=2)
        for x in (9,17):g.ellipse((x-2,11,x+2,15),fill=color)
    else:
        g.ellipse((3,3,23,23),outline=color,width=2)
        g.line((13,12,13,20),fill=color,width=2)
        g.ellipse((12,7,14,9),fill=color)
    glyph.save(OUT/("nav_"+icon+".png"),optimize=True)

print([(p.name,p.stat().st_size) for p in OUT.iterdir()])
