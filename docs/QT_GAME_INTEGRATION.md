# Qt Quick: game integration checkpoint

Continues PR #9 without merging it or changing the PR #8 branch.
The previous Windows test failed only at strict QML warnings: Windows native
controls do not support the customized content/background. Commit
15e3f9faceb23e5a26ff58f7a1832c33585994f4 forces Basic before QML is loaded.
Windows smoke run 45834226950 completed SUCCESS.

## New opt-in game actions

On Windows only:
```
python -m qt_experiment.quick --live-translation --game-hotkeys --config PATH --log LOG_PATH
```

- Reuses the existing KeyboardCapture hook with a new optional game-focus
  scope and explicit stop/unhook. The default Tk behaviour is unchanged.
- F8 toggles the native translation HUD, F9 opens a non-activating Win32 HUD
  for text input, Enter runs the existing semantic translator and sends the
  result through the existing CoD2 chat sender, Escape/F9 cancels.
- Focus loss, disabling F9, a stale translation or a translation error
  cannot trigger automatic sending. The existing sender now rechecks CoD2
  foreground before paste and Enter.
- F10 captures the CoD2 monitor through the existing screenshot infrastructure;
  there is no fallback to capturing the whole desktop if CoD2 is absent.
- No keyboard hook is started without the explicit flag. The manual
  translation workspace remains independent and never sends to the game.

## Evidence and limitations

Linux full regression: 229 passed, 3 skipped, 57 subtests passed.
The new test injects controlled hook events, verifies F8 and F10 dispatch,
F9 translation and sender handoff, focus-loss cancellation, and suppression
of a stale translation. The sender and native HUD are mocked in this
test; it does not send chat to a game. A Windows-only test checks actual
keyboard hook installation and termination; new Windows CI is required.
The owner's Windows machine is offline. Real F8/F9/F10 use in CoD2, DPI,
game FPS, overlay editing/fade, settings persistence, all other pages and
localization, artistic finish and installer remain outstanding.
This is an opt-in development integration, not a Windows RC.
