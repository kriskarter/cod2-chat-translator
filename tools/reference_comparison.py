"""Compare corresponding pixels from a 1536×830 QML client and the approved artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REGIONS = [
    ("Panorama / wordmark", (0, 0, 1536, 198)),
    ("Navigation", (0, 198, 1024, 248)),
    ("F8 / key / badge / route", (17, 277, 667, 447)),
    ("F9 / key / badge / route", (17, 468, 667, 638)),
    ("Server monitor / table", (680, 262, 1521, 458)),
    ("Roster / actions", (680, 458, 1521, 698)),
    ("HUD / Smart Engine / status", (287, 712, 1522, 807)),
]


def comparison(capture, destination):
    reference=Image.open(ROOT/"docs/images/server_monitor_rc/reference.png").convert("RGB").crop((0,34,1536,864))
    actual=Image.open(capture).convert("RGB")
    if actual.size != reference.size:
        raise ValueError("Capture must be exactly 1536 by 830 client pixels")
    sheet=Image.new("RGB",(1536,1600),"#171716")
    draw=ImageDraw.Draw(sheet)
    y=10
    draw.text((12,y),"Approved reference",fill="white")
    draw.text((778,y),"Running Qt application",fill="white")
    y+=22
    for label,box in REGIONS:
        draw.text((12,y),label,fill="#dcc69a")
        y+=18
        for x,source in ((0,reference),(768,actual)):
            crop=source.crop(box)
            crop.thumbnail((766,245),Image.Resampling.LANCZOS)
            sheet.paste(crop,(x,y))
        y+=crop.height+10
    sheet.crop((0,0,1536,y)).save(destination)


if __name__=="__main__":
    import sys
    comparison(*sys.argv[1:])
