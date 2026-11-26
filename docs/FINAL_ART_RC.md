# CoD2 Chat Translator v1.22.0 RC — visual and functional acceptance

Draft PR #8, branch `feature/premium-ui-redesign`. Artwork/code acceptance snapshot: `af280c29b2a2abab68ede26b922b2818d66614b1`. Screenshot/documentation commit follows it; no stable release or merge.

## Real application evidence

The images in `docs/images/final_art_rc/` are ffmpeg captures of the actual running Python/Tk application under Linux Xvfb, not generated interface mockups and not Windows captures. Eight pages: `xvfb_home.png`, `xvfb_servers.png`, `xvfb_translation.png`, `xvfb_overlay.png`, `xvfb_knowledge.png`, `xvfb_stats.png`, `xvfb_settings.png`, `xvfb_history.png`. Three actual dialogs: `xvfb_dialog_server.png`, `xvfb_dialog_about.png`, `xvfb_dialog_knowledge_dialog.png`. Extra captures: `xvfb_home_125pct.png` at 1536×864 simulated 125%, `xvfb_home_150pct.png` and `xvfb_dialog_server_150pct.png` at 1366×768 simulated 150%, `xvfb_home_1920.png` at 1920×1080.

The approved reference remains `docs/images/server_monitor_rc/reference.png`. Compared with it, the new header is one coherent city panorama rather than separately cut-out soldier/church assets; it shows the soldier's helmet, torso and gear, ruined streets and a complete church. Logo, stars, rule and caption remain distinct layers. Cards F8/F9 reveal separate artwork without opaque content rectangles. The steel texture continues between panels, and the extra field-gear illustration appears only on tall desktop screens. Navigation, monitor, lower rail and expert pages use the same restrained graphite/bronze palette.

Remaining visual differences from the reference: the subject is seen from behind instead of facing the viewer; the navigation and table still use styled Tk/ttk primitives, so selected rows remain a solid muted bronze rather than a true soft gradient; expert forms and modal dialogs are less richly composed than the Home page. The Windows native titlebar and controls may differ from these Linux captures.

## Verification

- `pytest -q`: 222 passed, 1 skipped (tested against the final visual code).
- `tools/smart_quality_check.py`: 32/32 authored semantic invariants; zero unsafe accepted, zero valid rejected. This is not measured live translation accuracy.
- Real application smoke: eight pages, three dialogs, RU/UK/EN, F8/F9 switches and keycap activation, overlay edit, Smart Engine, settings callbacks, preserved roster scroll. 1366×768 100%: Home content 490 px, viewport 495 px, no scroll. 1536×864 simulated 125%: content 541 px, viewport 578 px, no scroll. 1366×768 simulated 150%: content 512 px, viewport 535 px, no scroll and dialogs fit. 1920×1080: content 743 px, viewport 794 px, no scroll.
- A live UDP response from CLASSIC OBORONA `146.59.34.100:28960` reported online, map `mp_harbor`, 12/37 clients, 12 real player records, 37 ms server query in the sampled call. All 12 player ping fields were reported as 0 by the game server. The UI preserves that literal reported value in neutral color with a tooltip explaining that actual latency is unknown; it does not call it an ideal connection. Literal `^^` and unknown `^x` name sequences are retained, while recognized CoD2 color codes remain colored.
- A real Windows install, DPI behavior, F10 overlay atop the game, in-game hotkeys and CPU use during play are **unverified** because the owner's Windows machine was offline. Linux Xvfb is not a Windows substitute.

## Performance

Same VPS and isolated empty configuration at 1366×768 Xvfb. Single samples; CPU is process time, RSS is process peak. Previous RC `b2018feb` values were measured on the same host.

| Measurement | Previous RC | Final visual code |
| --- | ---: | ---: |
| Startup wall | 5.686 s | 5.412 s |
| Startup CPU | 3.221 s | 3.158 s |
| Startup peak RSS | 134.2 MiB | 134.5 MiB |
| Four seconds idle CPU | 0.593 s | 0.654 s |
| Peak RSS after idle | 142.0 MiB | 142.7 MiB |
| Four seconds after refresh CPU | 0.158 s | 0.139 s |
| Peak RSS after refresh | 142.0 MiB | 142.7 MiB |

The visual pass increased idle peak RSS by 0.7 MiB in this sample. No constant full-frame animation or extra server process was introduced. Windows runtime values and GPU memory remain unmeasured.
