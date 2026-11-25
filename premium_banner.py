"""Responsive illustrated banner assembled from independent art and logo assets.

Subject cutouts are fitted by height and composited after the panoramic city
backdrop. The bell tower and helmet cannot be clipped by a cover resize.
"""
from __future__ import annotations

from functools import lru_cache
from math import cos, pi, sin

from PIL import Image, ImageDraw


@lru_cache(maxsize=3)
def _source(name):
    from app import resource_path
    return Image.open(resource_path("assets/ui_premium/" + name)).convert("RGBA")


def _star(draw, x, y, radius):
    points=[]
    for index in range(10):
        angle=-pi/2+index*pi/5
        r=radius if index%2==0 else radius*.44
        points.append((round(x+cos(angle)*r), round(y+sin(angle)*r)))
    draw.polygon(points, fill=(201,153,76,225))
    draw.line(points+[points[0]], fill=(255,218,154,240), width=1)


@lru_cache(maxsize=16)
def compose_banner(width, height):
    width=max(480,int(width))
    height=max(120,int(height))
    source=_source("header_panorama.jpg")
    # Deliberately use the ruined *city* band: people and church are placed
    # separately below, at sizes that retain the full silhouettes.
    sx,sy=source.size
    city=source.crop((round(sx*.34),round(sy*.49),round(sx*.81),round(sy*.85)))
    scale=max(width/city.width,height/city.height)
    city=city.resize((round(city.width*scale),round(city.height*scale)),Image.Resampling.LANCZOS)
    x=max(0,(city.width-width)//2)
    y=max(0,(city.height-height)//2)
    result=city.crop((x,y,x+width,y+height)).convert("RGBA")

    # Preserve head, torso and pack while easing the rectangular boundary.
    soldier=source.crop((0,0,round(sx*.33),round(sy*.98)))
    soldier_h=height+35
    soldier_w=round(soldier.width*soldier_h/soldier.height)
    soldier=soldier.resize((soldier_w,soldier_h),Image.Resampling.LANCZOS)
    alpha=Image.new("L",(soldier_w,1))
    alpha.putdata([max(0,min(255,round(255*(soldier_w-x)/(soldier_w*.45))))
                   for x in range(soldier_w)])
    soldier.putalpha(alpha.resize((soldier_w,soldier_h)))
    result.alpha_composite(soldier,(round(width*.018),0))

    church=_source("church_subject.png")
    church=church.crop(church.getbbox())
    church_h=height-10
    church_w=round(church.width*church_h/church.height)
    church=church.resize((church_w,church_h),Image.Resampling.LANCZOS)
    result.alpha_composite(church,(width-church_w-round(width*.025),5))

    # Darken only the center for the separate live metallic wordmark.
    shade=Image.new("RGBA",(width,height),(0,0,0,0))
    band=Image.new("L",(width,1))
    center=width*.55
    band.putdata([round(96*max(0,1-abs(x-center)/(width*.31)))
                  for x in range(width)])
    shade.putalpha(band.resize((width,height)))
    result=Image.alpha_composite(result,shade)
    draw=ImageDraw.Draw(result,"RGBA")
    draw.line((0,height-3,width,height-3),fill=(11,10,9,230),width=3)
    draw.line((0,height-2,width,height-2),fill=(238,173,79,220),width=1)
    for fraction in (.335,.764):
        _star(draw,round(width*fraction),round(height*.35),max(7,round(height*.055)))
    return result
