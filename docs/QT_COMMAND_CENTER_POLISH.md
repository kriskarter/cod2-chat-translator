# Qt Preview: command center design pass

Continues PR #9, without changes to PR #8 or stable. Native Qt architecture and existing translation/UDP/hotkey implementations remain in use.

## Main page
- Existing panoramic scene and metallic logo retained; stars, amber divider, cropped full-width banner, compact secondary banner, application icon and best-effort Windows dark native caption.
- Thin rounded gradient metal controls, custom slider/scrollbar, dark inputs, amber selection.
- F8 and F9 have separate illustrations, live language selectors and meaningful runtime status. Manual translation is inside F9. Native overlay enabled at normal Windows startup unless saved otherwise.
- Server list uses content-dependent height; player roster has actual population, column headings, friend stars, original name colors and latency quality. Zero/unknown player latency is displayed as unavailable. Test fixture explicitly identifies itself as non-live.
- Lower bar shows real log/game/engine state, opens overlay settings, and keeps full diagnostics in tooltip.

## Secondary pages
All 11 pages remain. Added selected server summary, back navigation, localized style labels, compact scrollable pages, fixed save actions, HUD sample with drag positioning, empty states, session history timestamps and explicit JSON export/clear. The export contains chat text and nicknames and never overwrites an existing file or uploads automatically. About has logo, version, author, official repository, issue support and copyright link. Five real Qt dialogs can be captured with the evidence-only command line.
At compact secondary sizes the bottom bar is omitted to free work space; its controls remain on home/settings. This is a deliberate responsive layout decision, not feature removal.

## Verification and limits
The new regression checks real scene bounds and actual mouse clicks rather than accepting successful screenshot generation alone. The first pass eebfd0811937a486d6cb5a57bb0a58482bf3b9cd passed Linux (236 tests) but exposed F9 overflow on Windows. The final pass uses an anchored card body and explicit width constraints, plus fixes for compact secondary pages.
An actual Linux offscreen audit of the first pass produced 132 combinations with no QML warnings. 15-second warmed event-loop samples: visible CPU 2.6%, minimized CPU 1.7%, RSS 207.8 MiB; timer lateness p95 24.36/38.07 ms respectively. These are shared VPS measurements, not a native Windows game/FPS/GPU benchmark. The reproducible audit is qt_experiment/visual_audit.py.
Windows installer workflow captures all 11 pages, simulated 100/125/150% scale, compact secondary pages and five dialogs, and tests installing and launching the frozen EXE. Physical DPI, actual in-game input/overlay/FPS and owner artistic approval remain separate acceptance conditions. Qt update channel is still manual. Native HUD remains click-through; drag positioning is in the in-app sample, not direct manipulation of the live game overlay. Raw session history is not stored automatically. Some external diagnostics and native file chooser styling depend on the OS. Five Windows screenshots mentioned in the owner specification were not attached to the current request; the original reference and available prior screenshots were used.
