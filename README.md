# COD 2 Chat Translator

**A Windows chat translator for Call of Duty 2 Multiplayer that works while you play.**

CoD2 still has players from many countries, so mixed-language chat is pretty common.

COD 2 Chat Translator reads chat from `console_mp.log`, translates new messages and shows the result in a small overlay over the game.

No DLL injection and no game-memory modification.

## How it works

CoD2 can write its console output to `console_mp.log`. The translator watches new lines and filters player chat from map-loading output, dvars, file paths and other service messages.

When a player writes something, the app detects the source language, translates the message to your selected language and shows it in the overlay for a few seconds. The original message can also be shown if you want it.

## First launch

Install the app with `Setup.exe` and start it from the shortcut.

If CoD2 logging is not enabled yet, enter this once in the in-game console:

```text
/seta logfile 2
```

The app will try to find available logs automatically. If the one you need is missing, click **Add…** and select `console_mp.log` manually.

Choose the language you want to read and start playing.

> Translation requires an internet connection. Only the extracted chat-message text is sent to the online translation service.

## Servers and profiles

CoD2 servers with mods often use their own `fs_game` folders, which means different servers or mods may write chat to different files, for example:

```text
Call of Duty 2\main\console_mp.log
Call of Duty 2\example_mod\console_mp.log
Call of Duty 2\vetdm\console_mp.log
```

The app stores those paths as **profiles**. The first profile gets the neutral name **`Call of Duty 2`**, while additional mod profiles initially use their folder names. Any profile can be renamed manually.

**Automatic active-server detection** is enabled by default. While the translator is running, it periodically rescans the CoD2 folder. If joining a new server creates a new mod folder and its `console_mp.log` starts changing, the profile is added and selected automatically.

Only **one active log** is translated at a time. If several servers use the same mod folder, they share the same translator profile because the log path is the same.

Automatic detection can be disabled if you prefer to choose profiles manually.

## Overlay

The overlay can be moved, resized and tuned to stay out of the way.

You can change text size, background opacity, visible-message count and message lifetime. Ready-made presets are included as well.

After the overlay is locked, it becomes click-through so it does not steal the mouse from the game.

`F8` hides or shows the overlay without stopping translation.

## Gaming slang

Normal machine translation often struggles with short FPS chat, so common gaming terms are handled before regular translation.

Examples include `gg`, `wp`, `ns`, `nt`, `afk`, `brb`, `tk`, `nade`, `smoke`, `rush`, `camp`, `spawncamp`, `votekick`, `fps drop` and more.

There are three styles:

- **Clear** — simple wording without much gaming jargon.
- **Natural** — shorter wording closer to normal game chat.
- **Uncensored** — keeps rough language when the original is already rough. It does not add profanity to a neutral message.

## Languages

The source language is detected automatically. You only choose the language you want to read.

## Settings

The app remembers the selected profile, overlay position, text size, background, language, slang style and other options.

Installed-app settings are stored separately in:

```text
%APPDATA%\CoD2ChatTranslator
```

Updating the program should therefore keep your existing overlay setup and profile list.

## Updates

The app can check GitHub Releases for a newer version. Update packages are verified with SHA256 before installation, and the updater attempts to roll back replaced files if installation fails. If Setup is run over an older version that is still open, it closes the translator before replacing its files.

## Privacy

`console_mp.log` can contain more than chat, including server parameters or passwords.

**Do not publish the complete log.**

The app filters it locally and sends only the extracted chat-message text to the translation service.

## Build from source

For a local Windows build you need Python 3.12+ and Inno Setup.

Run:

```bat
BUILD_RELEASE.bat
```

GitHub Actions also builds and checks the Windows installer automatically.

## Project

Developer: **[kriskarter](https://github.com/kriskarter)**

If the app is useful, you can leave a ⭐ on the repository.

---

Unofficial fan-made utility. Not affiliated with or endorsed by Activision. Call of Duty and related marks belong to their respective owners.
