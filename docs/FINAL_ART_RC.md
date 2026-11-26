# CoD2 Chat Translator v1.22.0 RC — composition acceptance

Draft PR #8, branch `feature/premium-ui-redesign`; no stable release or merge. Base for this pass: `b2018feb4adfc58428b5e5bfef2a19aea94bb078`.

## Real application screenshots

`docs/images/final_art_rc/xvfb_*.png` contains 11 main screenshots taken by ffmpeg from the actual running Tk application at 1366×768 with Linux Xvfb. Pages: home, servers, translation, overlay, knowledge, stats, settings, history. Dialogs: server configuration, About, knowledge. The approved artistic reference is `docs/images/server_monitor_rc/reference.png`. An additional `xvfb_home_150pct.png` records the actual Tk application with simulated 150% scaling and vertical scrolling. These screenshots do not represent a Windows installation.

The new banner composes a distinct complete church and a larger soldier over a city panorama, preserving their aspect ratio. The logo is a separate asset and the subtitle is legible below it. The tab dividers sit between labels. The green F8/F9 and lower rail toggles remain live checkbuttons. The server list uses actual UDP observations; the five visible player rows are real data, with color runs preserved. A missing game journal is now explicitly signaled, and on Windows the game-window state is separately detected. All expert pages share the graphite palette; the history uses the same styled scrollbar; About uses the approved metallic logo.

Compared with the reference, the application still has simpler expert forms and no decorative crate/helmet in the compact Home. Its native Windows titlebar requests dark DWM chrome where supported. At 150% simulated Tk scale on 1366×768, Home scrolls to preserve live controls. Real Windows scale, titlebar and F10 overlay require native validation.

## Functional verification

- `pytest -q`: 221 passed, 1 skipped.
- Synthetic semantic safety checks: 32/32, zero unsafe accepted and zero valid rejected. This is not an actual in-game translation benchmark.
- Real application smoke at 1366×768, 1536×864 and 1920×1080; simulated 100%, 125%, 150% Tk scales; RU, UK and EN; navigation, F8/F9, settings and overlay callbacks, preserved player scroll. At 1366×768 / 100%, Home content is 490 px inside a 495 px viewport.
- Server/players in the screenshots came from a real CoD2 UDP query. An offline Windows computer was not touched. Native F10, installation and Windows DPI cannot be attested by Linux/Xvfb.

## Performance — same VPS, one run per revision

Python/Tk under 1366×768 Xvfb with empty isolated configuration. CPU measures seconds of process time; memory is peak resident set size in MiB. The previous RC values below were recorded for `b2018feb` on the same VPS. One-run results vary with host load.

| Phase | Previous RC `b2018feb` | This pass |
| --- | ---: | ---: |
| Startup wall time | 5.686 s | 3.594 s |
| Startup CPU time | 3.221 s | 3.039 s |
| Startup peak RSS | 134.2 MiB | 141.6 MiB |
| Four seconds idle, CPU | 0.593 s | 0.619 s |
| Peak RSS after idle | 142.0 MiB | 149.6 MiB |
| Four seconds following manual refresh, CPU | 0.158 s | 0.153 s |
| Peak RSS following refresh | 142.0 MiB | 149.6 MiB |

The additional independent full-height church asset increases resident memory by about 8 MiB in this sample; no continuous full-frame animation was added. Native Windows idle, in-game CPU and graphics memory remain unmeasured.
