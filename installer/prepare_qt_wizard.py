"""Compose Inno wizard bitmaps from the approved application artwork."""
from pathlib import Path
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1]
art = root / "qt_experiment/reference_art"
out = root / "installer/qt-wizard"
out.mkdir(exist_ok=True)
for scale in (1, 2):
    width, height = 164*scale, 314*scale
    canvas = ImageOps.fit(Image.open(art/"sheet.webp").convert("RGB"), (width,height))
    hero = ImageOps.fit(Image.open(art/"left.webp"), (width,138*scale), centering=(.48,.5))
    canvas.paste(hero,(0,0))
    logo = ImageOps.contain(Image.open(art/"brand.webp"), (width-8*scale,80*scale))
    canvas.paste(logo,((width-logo.width)//2,138*scale))
    kit = ImageOps.contain(Image.open(art/"field_kit.webp").convert("RGBA"),(width,108*scale))
    canvas.paste(kit,(0,height-kit.height),kit)
    canvas.save(out/f"welcome{scale}.bmp")
    icon = Image.open(root/"assets/app.ico").convert("RGBA").resize((49*scale,49*scale),Image.Resampling.LANCZOS)
    tile = Image.new("RGB",icon.size,"#242521")
    tile.paste(icon,mask=icon.getchannel("A"))
    tile.save(out/f"icon{scale}.bmp")
