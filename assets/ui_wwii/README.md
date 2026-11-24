# WWII GUI artwork — source and license

All images in this directory are backgrounds or icons, never interactive
controls or simulated program statuses.

Historical photograph: SC 192042 — U.S. tanks pass through the wrecked streets
of Coutances, France, on their way to the sea beyond the town, 30 July 1944.

Photographer: U.S. Army. Wikimedia Commons source:
https://commons.wikimedia.org/wiki/File:SC_192042_-_U.S._tanks_pass_through_the_wrecked_streets_of_Coutances,_France,_on_their_way_to_the_sea_beyond_the_town._30_July,_1944.jpg

Identified on Commons as public domain: created by an employee of the
U.S. Army in official duties. It is an archival image, NOT a screenshot
from Call of Duty 2, nor an indicator of a connected server.

The reduced source copy is source_coutances.jpg. Generated overlays, other
raster assets, metal textures and original menu glyphs are produced by
tools/build_wwii_assets.py (Pillow at build-time only). Runtime loads
raster files using tkinter.PhotoImage. No font files are bundled.


## RC3 original product artwork

The brand_logo.png and brand_logo_compact.png assets are original metallic
wordmarks with an illustrated camouflage-net WWII helmet. The generator
uses locally installed system fonts as raster sources: NO FONT FILE IS BUNDLED.
switch_on.png and switch_off.png are state icons on real, keyboard-accessible
Tk Checkbutton controls. quick_*.png decorate actual native buttons.
version_plate.png is a blank badge with the real version drawn at runtime.
body_backdrop.png is a dim archival photo treatment, never a live status.

All generated assets can be rebuilt with:
    python tools/build_wwii_assets.py
Runtime Windows builds load PNGs using tkinter.PhotoImage (no Pillow dependency).
