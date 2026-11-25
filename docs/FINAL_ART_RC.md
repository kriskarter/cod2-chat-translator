# CoD2 Chat Translator v1.22.0 RC — visual and functional acceptance

Base: `61ab2679b4ac4d34d721e4002c5485f199d5add4`. Existing draft PR #8; stable branch unchanged.

## Real running application

All images in `docs/images/final_art_rc/` are screenshots captured with ffmpeg from the actual Tk application under Linux/Xvfb at 1366×768. They are not generated concepts or Windows captures. The design reference remains `docs/images/server_monitor_rc/reference.png`.

- `xvfb_home.png` — distinct illustrated F8 town and F9 tank; no opaque content frame, live controls, one soldier with torso in panoramic header, continuous navigation and functional bottom rail.
- `xvfb_servers.png`, `xvfb_translation.png`, `xvfb_overlay.png`, `xvfb_settings.png`, `xvfb_history.png`, `xvfb_knowledge.png`, `xvfb_stats.png` — other live pages.
- `xvfb_dialog_server.png`, `xvfb_dialog_about.png`, `xvfb_dialog_knowledge_dialog.png` — actual dialogs.

## Behavior checked

- pytest: 221 passed, 1 skipped.
- Xvfb smoke: five live navigation controls; eight pages; F8/F9 keyboard-facing illustrated keys and actual switches; RU/UK/EN; settings callbacks; 1050px layout; 1366×768 Home with no vertical scrolling in simulated 100% Tk scaling.
- Player roster refresh now preserves scroll position and skips unchanged contents. Server lists preserve selection and scroll. Added live smoke assertion with 32 players and one joining.
- The monitor queried real CoD2 UDP data from CLASSIC OBORONA on the VPS during capture. Names, scores, ping, map and status in screenshots are observed responses at capture time, not bundled sample data.
- F10 in-game overlay, Windows native DPI and player notifications were not validated on Windows in this environment. The owner's prior installed Windows screenshot refers to the previous SHA.

## Performance comparison

Same VPS, Python 3.12/Tk 8.6, 1366×768 Xvfb, temporary empty configuration; one measured run per revision. CPU uses process time in seconds; memory uses peak resident set size in MiB.

| Phase | Previous RC `61ab267` | New UI |
| --- | ---: | ---: |
| First window initialized, elapsed | 4.616 s | 5.686 s |
| First window initialized, CPU | 2.792 s | 3.221 s |
| Peak RSS at initialized window | 133.3 MiB | 134.2 MiB |
| Four seconds idle, CPU | 0.631 s | 0.593 s |
| Peak RSS after idle | 142.5 MiB | 142.0 MiB |
| Four seconds after manual refresh, CPU | 0.144 s | 0.158 s |
| Peak RSS after refresh | 142.5 MiB | 142.0 MiB |

The artwork adds about 1.1 s to cold startup in this sample, while idle and refresh CPU and memory remain close to baseline. This is a Linux/Xvfb measurement, not a native Windows or in-game benchmark.

## Visual comparison with approved reference

The separate logo, single helmet-and-backpack soldier, unified metal navigation, different F8/F9 scenes, drawn-on-art text, visible tank, metal keycaps, status rail and live server tables now follow the reference composition. The accepted reference has a custom dark titlebar and additional helmet/crate decoration. The application requests a dark native DWM titlebar on Windows where supported, retaining native resize, taskbar and system shortcuts; this requires confirmation on the owner's Windows install. The compact layout hides secondary decoration. Tk comboboxes, text inputs and some expert pages retain simple rectangular controls; final artistic approval is the owner's decision after a new native Windows install.

The RC installer is a test artifact from Windows GitHub Actions; no stable Release was published and PR #8 remains draft.
