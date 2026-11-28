# Qt Quick premium UI — implementation checkpoint (not an RC)

Base experiment: `9ddb83410e3a72498d0aae7a945788fbfe4d6a7a`. Work stays on
`experiment/qt-premium-game-ui`; PR #9 remains draft. Tk application entry
point and the Widgets comparison remain available and unmodified.

## Implemented
- Fifteen named reusable QML controls (MetalPanel, MetalButton, AmberButton,
  KeycapButton, TranslationCard, TacticalSwitch, NavigationTab, LanguageSelector,
  ServerTable, PlayerRoster, FriendIndicator, MetalScrollBar, OverlayControl,
  SmartEngineControl, SystemStatusPanel, MetalDialog).
- Home uses existing RC frame/metal/amber/keycap/switch/selection textures with
  BorderImage slicing matching the previous Tk resource margins. It uses the
  original integrated command panorama and gold-2 logo, separate artwork for
  F8 and F9, shared table header/row layout, and newly authored SVG icons.
  No bottom helmet/backpack decoration.
- Qt monitor mode uses the existing UDP Monitor, not a synthetic source:
  worker snapshots cross into the Qt thread through a queued signal.
  Real refresh, session-only server addition, configured friends online count,
  and Windows game launch with an explicitly supplied executable.
  Config files are read only; there is no user-settings migration here.
  Unmigrated translation and overlay controls are disabled in live mode.
- Demo remains clearly labeled, with the same explicit synthetic comparison
  dataset and no real game actions.

## Running
```
python -m qt_experiment.quick
python -m qt_experiment.quick --gallery
python -m qt_experiment.quick --live-monitor --config PATH_TO_CONFIG_JSON
python -m qt_experiment.quick --live-monitor --game-exe PATH_TO_COD2MP_EXE
```

Screenshots are actual Linux software/offscreen window renders of the demo:
[900×620](images/qt_rc_progress/home_900x620.png),
[1366×768](images/qt_rc_progress/home_1366x768.png),
[1536×864](images/qt_rc_progress/home_1536x864.png),
[1920×1080](images/qt_rc_progress/home_1920x1080.png),
[component dialog](images/qt_rc_progress/components_dialog.png).
They are not Windows screenshots and do not imply visual acceptance.
The original [artistic reference](images/server_monitor_rc/reference.png)
remains the target. Current assets reproduce its metal/amber palette and
hierarchy but the full reference-level finish is not achieved; the current
logo composition and card details differ.

## Verification
Linux: PySide6 6.8.3; full pytest **226 passed, 1 skipped, 57 subtests passed**.
The new runtime test renders at four client sizes, sends actual Qt mouse
clicks to F8, switch and overlay in the demo, and exercises a real loopback UDP
response through Monitor and queued Qt delivery. It checks player data, friend
count, disabled translation state, duplicate rejection, and unchanged config.
This is not a live remote server or CoD2 test.

Five cold process + rendered-frame samples on the shared Linux VPS:
2911, 2322, 1298, 1537, 1330 ms; median 1537 ms; observed median peak RSS
99.9 MiB. These measurements include screenshot capture and are sensitive to
shared VPS load. They are **not** a fair comparison with the full Tk program.
GPU, Windows DPI, game FPS, and full-app latency have not been measured.

A dedicated Windows smoke workflow is scoped to this experimental branch.
It is not the existing stable installer workflow and does not build an RC.

## Release blockers
The entire incoming/outgoing translation lifecycle, F8/F9/F10 global keys,
native overlay, Smart Engine, full favorites/persistence, profiles, history,
knowledge, notifications, updater, remaining pages and dialogs, RU/UK/EN,
Windows DPI/CoD2 acceptance, licensing and the full installer are not migrated
or verified. Do not label this checkpoint a Windows RC or ship it to stable.
