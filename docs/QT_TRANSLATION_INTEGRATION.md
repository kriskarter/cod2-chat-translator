# Qt Quick translation integration checkpoint — not a release candidate

Continues 3595228d36495a207abc515aa53992afe7caf5b2. PR #9 stays draft.
The existing Tk app, PR #8 and stable entry point are unchanged.

## Implemented
- Opt-in `python -m qt_experiment.quick --live-translation --config PATH --log LOG_PATH`.
  Configuration and installed knowledge are read, not written. No Tk root or
  widgets are created. The existing ControlApp ingress methods, LogTailer,
  bounded two-worker TranslatorWorker pool, Smart Engine, bundled knowledge
  pack and existing F9 translation dispatcher are reused.
- Working incoming translation, deduplication and stale-result rejection;
  a bounded 200-message in-session history, manual log and target selection,
  Smart Engine switch and a manual outgoing translation workspace.
  Manual outgoing does not inject keystrokes or send to CoD2.
- Qt owns a thin native HUD lifecycle using existing Win32LayeredOverlay:
  enabled only on Windows, explicit opt-in, bounded messages and expiry,
  native render/hide/destroy. Existing renderer is not rewritten.
- Remaining Tk UI and Widgets comparison are retained.

## Evidence
Full Linux pytest: 228 passed, 2 skipped, 57 subtests passed.
Runtime integration test appends a new message to a temporary CoD2 log,
runs the real parser and Smart Engine, verifies the Russian translation,
navigates to actual QML history/settings/outgoing pages and verifies a
local outgoing translation without contacting the online provider.
Checks stale result rejection and unchanged config. HUD lifecycle test
uses a mock surface on Linux; actual HWND test is Windows-only.
The following are real Linux offscreen screenshots with test input:
[history](images/qt_translation_progress/translation_history.png),
[settings](images/qt_translation_progress/translation_settings.png),
[outgoing](images/qt_translation_progress/translation_outgoing.png).

## Outstanding
Global F8/F9/F10 hook integration, automatic F9 game sending, F10 screenshot
capture, auto profile switching, settings persistence, full language list
and UI localization, remaining pages, history persistence, full favorite
editing, notifications, update, HUD edit/fade and actual CoD2 compatibility,
artistic refinement, hardware performance and Windows packaging/installer.
The real native HUD smoke test is added to Windows CI but no game or
hardware acceptance is implied. No RC or EXE is claimed.
