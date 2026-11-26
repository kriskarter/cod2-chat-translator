# Qt server workspace and isolated settings

PR #9 remains draft. The original Tk configuration is imported read-only.
Use a distinct settings file, e.g.:
```
python -m qt_experiment.quick --live-translation --game-hotkeys --config config.json --settings-file qt_settings.json
```
The optional Qt settings file is read on startup and written only via the
explicit Save settings button. The source config is not overwritten.
Writes use an atomic replacement and reject changes detected in the file
since it was opened. Unknown imported configuration keys are retained.

The server workspace uses the existing Monitor and supports server add,
label editing, favorites, removal with confirmation, live player roster,
refresh, connect and favorite-player management. The full existing list
of incoming target languages is available in Qt. Session-only mode remains
available without specifying a settings file.

Evidence: full Linux regression 230 passed, 3 skipped, 57 subtests passed.
A real QML workspace render and tests verify CRUD, selection, favorites,
deduplication of player names, save/reload format, unchanged original config,
and rejection of an externally modified settings file.
[Server page screenshot](images/qt_settings_progress/server_workspace.png).
This is a development checkpoint. Full profile discovery/auto-switching,
notification/update integration, complete UI localization, artistic
acceptance, native game/DPI/performance acceptance and installer still
remain open.
