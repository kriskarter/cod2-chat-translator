# Qt Preview / PR 9: integration and release evidence

The Qt executable and installer are isolated from the stable Tk installation.
Existing PR 8 and stable entry point are unchanged. PR 9 remains draft.

## Implemented
- Qt Quick artwork: original command panorama, extracted metallic gold-2 logo, slimmer nine-slice frames, dark fields, improved switches, responsive navigation and secondary pages. Qt Widgets remains the comparison reserve.
- Existing log parser, bounded translation workers, Smart Engine, knowledge runtime, UDP server monitor, favorites and native Windows HUD are retained.
- Qt settings import is read-only for the prior application; explicit saves use an isolated atomic JSON file. F9 language pair and enablement are imported/persisted.
- F9 has a debounced live preview, stale-result rejection, focus-scoped key handling and Enter-only game sending. F8 toggles the layered HUD; F10 captures game monitor.
- Profile discovery and activity-driven switching reuse existing helpers, including starting at the previous log size. Periodic discovery is bounded. Game logfile configuration is an explicit confirmed action, deferring running-game changes.
- HUD settings include size, position, font, message count, TTL, opacity, auto-height, background and fade options, test/clear/reset and three presets.
- Qt pages for home, servers, settings, history, manual outgoing, profiles, knowledge, notifications, statistics, overlay and about/update. RU/UK/EN labels, separate installer language selection. Existing opt-in local experience collection/cache/stats/export/clear.
- Separate Qt preview update discovery only offers the official GitHub prerelease page, not automatic replacement or execution of stable packages.

## Verification
Linux full regression on this working tree: 235 passed, 3 skipped, 57 subtests passed.
Previous commit 2b3662977dd5c2007bec63677e87d93b09573fae: actual Qt runtime rendered 132 combinations (11 pages × 3 languages × 4 logical sizes, 1366×768, 1536×864, 1920×1080, 900×500), no warnings during navigation. On shared VPS software rendering: first frame 2214 ms, idle process CPU 4.2%, RSS 185.2 MiB after matrix, median page render + screenshot 76.1 ms, p95 410.9 ms. These are not native Windows FPS, UI event latency or a comparison with full Tk application. Explicit engine teardown was added afterwards.
First independent Windows installer passed freeze, smoke, actual installation, launch and isolated prerelease publishing:
https://github.com/kriskarter/cod2-chat-translator/actions/runs/45839320818
The latest workflow additionally runs a simulated Qt scale matrix, not physical monitor DPI acceptance.

## Remaining acceptance
This is an installable isolated Qt preview, not a stable release. The owner's Windows machine was offline. Real CoD2 global key, overlay, focus, game FPS and actual display DPI must be independently accepted. The new HUD position editor uses coordinates and reset, not interactive drag of the native click-through surface. Preview updater offers a manual official download, not silent auto-update; history remains session-bound unless opt-in local experience is enabled. Some dynamic diagnostics can remain in their original language. Visual acceptance is explicitly reserved for the owner. No claim of full equivalence to every legacy dialog, native performance or artistic perfection.
