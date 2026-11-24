# Premium UI artwork and implementation

The owner's attached approved WWII concept is the visual direction for this
artwork. The three `*_source.png` files were generated specifically for this
project from that reference: a cinematic panorama, a transparent brand
wordmark, and an aged steel material sample. They contain no sampled UI
screenshots, real status values, or interactive controls. The source PNGs
are retained so the generated component assets can be rebuilt.

`python tools/build_premium_ui.py` exports the header, independent wordmark,
server/overlay scene miniatures, metal heading strip, switch illustrations,
and button surfaces in normal, hover, pressed and disabled states under
`assets/ui_wwii/`. Buttons are ttk image elements with nine-slice borders;
text, labels, actions and accessibility states remain actual widgets.

The application keeps the Tk backend and existing F8/F9/overlay callbacks.
This preserves the already integrated Windows overlay and PyInstaller path,
while the image-backed ttk controls deliver scalable illustrated materials.
No third-party font or external image is required for these three source PNGs.

Illustrated output must be reviewed on actual Windows DPI settings in
addition to the automated Linux Tk layout checks; neither test stands in
for an in-game CoD2 interaction test.
