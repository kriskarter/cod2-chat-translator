"""Extract independent Qt skins from the approved 1536×864 artwork (source pixels)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qt_experiment/reference_art"
OUT.mkdir(exist_ok=True)
ref = Image.open(ROOT / "docs/images/server_monitor_rc/reference.png").convert("RGB")
plates = Image.open(ROOT / "assets/qt_art/source/restored_card_plates.webp").convert("RGB")
assert ref.size == (1536, 864)


def save(name, im):
    im.save(OUT / name, **({"quality": 94, "method": 6} if name.endswith("webp") else {"optimize": True}))


# Preserve the complete approved panorama as one lossless asset; the legacy slices remain available.
ref.crop((1, 34, 1535, 232)).save(OUT / "panorama.webp", lossless=True, method=6)
for part, x1, x2 in (("left", 1, 520), ("wordmark", 520, 1103), ("right", 1103, 1535)):
    save(part + ".webp", ref.crop((x1, 34, x2, 232)))
for key, y in (("f8", 311), ("f9", 502)):
    card = ref.crop((17, y, 667, y + 170))
    backing = plates.crop((1, y - 300, 651, y - 130))
    mask = Image.new("L", card.size)
    draw = ImageDraw.Draw(mask)
    for rect in ((15, 16, 151, 153), (162, 20, 500, 101),
                 (159, 104, 379, 147), (501, 17, 636, 68)):
        draw.rectangle(rect, fill=255)
    card = Image.composite(backing, card, mask.filter(ImageFilter.GaussianBlur(2)))
    save(key + "_plate.webp", card.crop((9, 8, 641, 162)))
    # F8 / F9 are invariant key legends. The actual Button carries its accessible name.
    cap = ref.crop((31, y + 20, 171, y + 155)).convert("RGBA")
    alpha = Image.new("L", cap.size)
    ImageDraw.Draw(alpha).polygon([(20,7),(112,7),(134,17),(133,38),(123,119),
                                   (117,131),(10,129),(2,113),(14,19)],fill=255)
    cap.putalpha(alpha.filter(ImageFilter.GaussianBlur(3)))
    save(key + "_cap.png",cap)


def frame(name, box, corner, thickness):
    im = ref.crop(box).convert("RGBA")
    w,h = im.size
    mask = Image.new("L", im.size)
    d = ImageDraw.Draw(mask)
    d.polygon([(0,corner),(corner,0),(w-corner,0),(w-1,corner),(w-1,h-corner),
               (w-corner,h-1),(corner,h-1),(0,h-corner)],fill=255)
    d.rounded_rectangle((thickness,thickness,w-thickness-1,h-thickness-1),radius=corner//2,fill=0)
    im = Image.composite(im, Image.new("RGBA", im.size), mask)
    # Sample all four corner joints at native scale and keep the long-edge patina.
    save(name,im)

frame("frame.png",(680,296,1521,732),10,7)
frame("card_frame.png",(17,311,667,481),10,5)
frame("console_frame.png",(287,746,1522,841),10,8)


def clean_plate(name, box, left, right):
    # Rebuild the blank span from vertical samples just inside the two end caps.
    im = ref.crop(box)
    w,h = im.size
    strip = im.crop((left-1,0,left,h)).resize((2,h))
    strip.paste(im.crop((right,0,right+1,h)),(1,0))
    im.paste(strip.resize((right-left,h),Image.Resampling.BILINEAR),(left,0))
    save(name, im)

clean_plate("button_steel.png",(703,670,965,717),31,237)
clean_plate("button_amber.png",(1224,669,1509,719),31,253)
clean_plate("nav_on.png",(23,232,203,281),25,160)
clean_plate("badge.png",(523,336,647,374),9,116)
clean_plate("selected_row.png",(692,390,1509,426),12,807)
clean_plate("toggle.png",(604,767,681,796),12,71)
save("green_lamp.png",ref.crop((654,772,673,791)))

for name,box in {
    "home":(55,240,85,270),"servers":(235,241,265,270),"settings":(409,239,441,272),
    "history":(596,241,627,271),"about":(809,240,841,271),"antenna":(702,308,743,351),
    "friends":(1327,316,1356,342),"hud":(328,768,378,813),"chip":(733,767,780,814),
    "star":(706,396,730,420),"chat":(189,418,221,448),"check":(534,340,565,370),
    "ready":(1178,770,1220,811),"add":(747,680,772,707),"refresh":(1033,679,1060,708),
    "connect":(1280,681,1304,708)}.items():
    im=ref.crop(box).convert("RGBA")
    # Estimate the local background of each scanline from its outside edges.
    pix=im.load()
    for y in range(im.height):
        bg=tuple((pix[0,y][i]+pix[im.width-1,y][i])/2 for i in range(3))
        for x in range(im.width):
            rgb=pix[x,y][:3]
            a=min(1,max(0,(max(v-b for v,b in zip(rgb,bg))-7)/54))
            pix[x,y]=tuple(round(min(255,max(0,(v-(1-a)*b)/a))) if a else 0 for v,b in zip(rgb,bg))+(round(255*a),)
    save(name+".png",im)

for name, box in (("body",(322,679,656,741)),("panel",(1045,306,1304,353)),
                  ("nav",(1043,236,1353,278)),("field",(1080,444,1150,460))):
    tile=ref.crop(box)
    mirrored=Image.new("RGB",(2*tile.width,2*tile.height))
    mirrored.paste(tile,(0,0));mirrored.paste(ImageOps.mirror(tile),(tile.width,0))
    mirrored.paste(ImageOps.flip(mirrored.crop((0,0,mirrored.width,tile.height))),(0,tile.height))
    save(name+".webp",mirrored)
