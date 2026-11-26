# Qt Preview — friends and player presence

PR #9, existing experiment/qt-premium-game-ui. Stable and PR #8 are not modified.

## User workflows
- Click grey/gold stars on home and server workspace rosters. Right-click a nickname for add/remove, plain nickname and server-address copy, or connection to that tracked server.
- The clickable presence indicator opens an in-app graphite panel, online matches first, unknown and offline differentiated; matching rows include original color-coded nickname, server, map, population and connection action.
- Friend mutations and notification preferences auto-save atomically to isolated Qt settings, preserving existing saved unrelated settings and leaving the imported legacy configuration read-only. External file changes cancel the save and roll back the mutation. Manual additions remain.
- Notifications: separate master, arrival, departure, possible move and optional sound. Sound defaults off; the short bundled two-tone WAV is played asynchronously on Windows, throttled to avoid bursts. In-app notice is custom QML; when inactive the existing native Windows notification route is used silently, subject to OS notification settings.
- Monitoring reuses the same worker and UDP polling interval (30–600 seconds, default 60); it continues without CoD2 running and with minimized Qt. No extra UDP requests for friends.

## Evidence and limits
Presence is by normalized nickname, not a verified identity. Color markup is parsed once; literal carets and Unicode case/normalization work. Raw display colors are preserved and HTML escaped. Multiple matches are visibly ambiguous. Two successful observations confirm a change; adjacent-round move halves are combined when supported, otherwise report only observed server-specific changes. Timeouts and limited responses invalidate that server's baseline silently; a reconnect does not generate false departure/rejoin notifications. Absence across all successfully queried tracked servers is offline, incomplete coverage is unknown. Events during an outage may be missed; confirmation can take multiple polling intervals. Offline does not mean a player is absent from every CoD2 server globally.

Linux full regression: 244 passed, 3 skipped, 57 subtests. Real Qt mouse actions test both stars, context menu, clipboard, panel, mocked connection target, restart persistence, external-write rollback; real loopback UDP tests two independent servers while the actual Qt window is minimized and verify no extra requests, join/move/leave options, sound dispatch and no duplicates. Pure presence tests cover escaped color codes, same-name ambiguity, two rounds, outage, and adjacent-round move. Worst-case synthetic CPU calculation with 32 servers / 4096 player rows / 100 friends: median 94.95ms, max 128.71ms per round on the shared VPS, not a Windows hardware measurement. Actual live mode contains no fixture data. Screenshots in this report and CI use explicitly labeled test fixtures.
Windows physical game connection, audible sound, actual DPI/FPS and owner artistic acceptance still require native testing.
