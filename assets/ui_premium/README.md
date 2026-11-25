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

`console_chassis.png` and `generic_panel.png` were newly generated for this
project from the owner's approved concept on 24 November 2026. The first is
the empty two-bay Home chassis with illustrated scout/radio operator and an
empty in-game scene; the second is a reusable blank metal panel. Neither
contains interface text, numeric values, buttons or state. `premium_home.py`
places actual Tk controls above the chassis and scales it with the window.
These authored assets are distinct from the old v1.21.3 screenshots and do
not incorporate stock photography or a third-party font.

`translation_chassis.png` is another blank graphic generated from the same
approved direction for the expert F8/F9 screen. It has two illustrated bays,
no baked UI text or state. `premium_translation.py` binds live controls above
it. `premium_generic_frame.png` is the 160×160 nine-slice export from the
generic source with 42px borders for expandable expert panels and dialogs.

Illustrated output must be reviewed on actual Windows DPI settings in
addition to the automated Linux Tk layout checks; neither test stands in
for an in-game CoD2 interaction test.
# Server Monitor command center artwork

The 1.22.0 command center uses `monitor_hero.png` (panoramic battlefield
background) and `monitor_logo.png` (transparent two-line metallic logo).
They were generated specifically for this project from the owner's approved
composition. Neither resource contains controls, telemetry, player names or
server status. They remain separate assets rendered beneath live Tk widgets.

The original supplied concept is a design reference only. Its sample server
rows and player statistics are never bundled into the running app.

