# COD 2 Chat Translator

**A small Windows app that translates Call of Duty 2 multiplayer chat while you play.**

[Русское описание](README_RU.md)

I made this for a simple reason: CoD2 servers are still full of players from different countries, and chat can turn into a mix of English, Polish, Russian, Ukrainian, German and everything in between.

COD 2 Chat Translator reads the game's own `console_mp.log`, picks out chat messages, translates them and shows the result in a small overlay over the game.

No DLL injection. No game-memory modification.

## How it works

1. CoD2 writes console output to `console_mp.log`.
2. The app watches new lines and ignores map-loading spam, dvars and other service output.
3. When it finds a chat message, it detects the language and translates the message to the language you selected.
4. The translation appears in the overlay for a few seconds.

The original message can also be shown if you want it.

## Setup

Download the latest Windows installer from **Releases** and run it.

If CoD2 logging is not enabled yet, open the in-game console and enter:

```text
/seta logfile 2
```

On the first launch the app tries to find `console_mp.log` automatically. If it misses your CoD2 folder, use **Browse** and select the file yourself.

That's it: choose the language you want to read and start playing.

> Translation uses an online translation service, so an internet connection is required.

## Overlay

The overlay is meant to stay out of the way while you play.

You can change the text size, background opacity, number of visible messages and how long they stay on screen. There are also a few ready-made presets if you do not want to tune everything by hand.

Use **Configure overlay** to move or resize it. Once fixed, the overlay becomes click-through so it does not steal the mouse from the game.

`F8` hides or shows the overlay without stopping translation.

## Gaming slang

Short FPS chat is not normal prose, so common gaming terms are handled before the regular translation.

Examples include `gg`, `wp`, `ns`, `nt`, `afk`, `brb`, `tk`, `nade`, `smoke`, `rush`, `camp`, `spawncamp`, `votekick`, `fps drop` and more.

There are three styles:

- **Clear** — easier to understand if you are not used to gaming slang.
- **Live** — shorter, more natural game-chat wording.
- **Uncensored** — keeps the rough tone when the original message is already rough. It does not add profanity to a neutral message.

## Languages

The source language is detected automatically. You only choose the language you want to read.

So a Russian message can be translated to English, an English message to Ukrainian, Polish to German, and so on.

## Updates

The app can check GitHub Releases for a newer version.

Update packages are verified with SHA256 before installation. The updater also keeps user settings separate from program files, so updating should not reset your overlay or language settings.

## Privacy

`console_mp.log` may contain more than chat — for example server parameters or passwords.

**Do not upload or publish the whole log.**

The app filters the log locally and sends only the extracted chat-message text to the translation service.

## Build from source

For a local Windows build you need Python 3.12+ and Inno Setup.

Run:

```bat
BUILD_RELEASE.bat
```

GitHub Actions also builds the Windows installer automatically.

## Project

Developer: **[kriskarter](https://github.com/kriskarter)**

If the app is useful, a ⭐ on the repository helps other CoD2 players find it.

---

Unofficial fan-made utility. Not affiliated with or endorsed by Activision. Call of Duty and related marks belong to their respective owners.
