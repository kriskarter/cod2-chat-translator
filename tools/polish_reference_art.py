"""Rebuild standalone decoration and clean large materials from the approved artwork."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

root = Path(__file__).resolve().parents[1]
out = root / "qt_experiment/reference_art"
source = Image.open(root / "docs/images/server_monitor_rc/reference.png").convert("RGB")

# Trace the visible equipment silhouette in the original bottom-left corner.
gear = source.crop((0, 673, 310, 864)).convert("RGBA")
points = [(0,23),(6,18),(19,12),(40,8),(58,7),(77,11),(92,18),(105,31),
          (115,50),(122,66),(134,67),(138,63),(154,65),(179,62),(191,63),
          (204,69),(215,72),(232,74),(247,78),(266,82),(278,92),(281,109),
          (286,126),(294,149),(298,171),(306,191),(0,191)]
matte = Image.new("L", gear.size)
ImageDraw.Draw(matte).polygon(points, fill=255)
gear.putalpha(matte.filter(ImageFilter.GaussianBlur(1.25)))
gear.save(out / "field_kit.webp", lossless=True, method=6)

# Isolate the two line wordmark and stars. Keep dark pits in the lettering by
# extending the matte inward from local luminance edges instead of a global key.
logo = source.crop((520,34,1100,185)).convert("RGBA")
luma = np.asarray(logo.convert("L"),dtype=float)
support = Image.new("L",logo.size)
d = ImageDraw.Draw(support)
for poly in [[(150,4),(380,4),(379,76),(150,76)],[(4,79),(571,79),(567,143),(1,143)],
             [(101,29),(139,29),(139,65),(101,65)],[(399,29),(437,29),(437,65),(399,65)]]:
    d.polygon(poly,fill=255)
a = Image.fromarray(np.uint8(np.clip((luma-56)*4,0,255)))
a = ImageChops.multiply(a,support)
a = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.45))
logo.putalpha(a)
logo.save(out / "brand.webp", lossless=True,method=6)

# Sample only the unlettered body beside the cards. Build a full-width plate
# from its color statistics with nonperiodic grain at three spatial scales.
rng = np.random.default_rng(1945)
sample=np.asarray(source.crop((330,680,654,739))).reshape(-1,3)
tone=np.median(sample,axis=0)
def grain(w,h,scale):
    noise=Image.fromarray(rng.integers(0,256,((h+scale-1)//scale+1,(w+scale-1)//scale+1),dtype=np.uint8))
    return (np.asarray(noise.resize((w,h),Image.Resampling.BICUBIC)).astype(float)-127)/70
for name,w,h,offset,strength in (("sheet",1344,672,0,1),("inset",512,80,-6,.36)):
    y,x=np.mgrid[:h,:w]
    variation=.7*grain(w,h,1)+1.2*grain(w,h,3)+1.6*grain(w,h,38)+2.8*grain(w,h,163)
    light=1.5-3*((x/w-.42)**2+(y/h-.32)**2)
    rgb=tone + offset + (strength*(variation+light))[:,:,None]
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(out/(name+".webp"),quality=89,method=6)
