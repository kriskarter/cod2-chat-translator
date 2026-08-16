# COD 2 Chat Translator

**Real-time multiplayer chat translation overlay for Call of Duty 2.**  
**Разработчик / Developer:** [kriskarter](https://github.com/kriskarter)

> Unofficial fan-made utility. Not affiliated with or endorsed by Activision. Call of Duty and related marks belong to their respective owners.

## What it does

COD 2 Chat Translator watches the local `console_mp.log`, extracts only chat messages, detects the source language automatically, translates them to the language selected by the player, and displays the result in a compact click-through overlay over the game.

It does **not** inject a DLL into the game and does not modify game memory.

### Highlights

- automatic source-language detection;
- Russian and English application interface;
- translation to many target languages;
- compact draggable overlay with adjustable text size, background opacity and lifetime;
- gaming-slang handling for common CoD/FPS abbreviations such as `gg`, `wp`, `ns`, `afk`, `camp`, `rush`, `spawn`, `nade`, `tk` and more;
- three slang styles: clear, live, and uncensored-preserving;
- bilingual Windows installer (`Русский / English`);
- settings stored in `%APPDATA%\\CoD2ChatTranslator` so updates do not overwrite them;
- built-in GitHub Release update checker with SHA256 verification and rollback support;
- Windows builds produced by GitHub Actions.

## Install

Download the latest Windows installer from **Releases** and run:

`CoD2ChatTranslator_Setup_vX.Y.Z.exe`

On first use, enable CoD2 console logging if needed:

```text
/seta logfile 2
```

If the program cannot locate `console_mp.log` automatically, select it manually.

## Privacy

`console_mp.log` can contain service parameters and server passwords. **Do not publish the full log.** The application filters the file locally and sends only the extracted chat-message text to the translation service.

## Updates

The application checks the latest GitHub Release. Update packages include a SHA256 hash; the updater verifies the package before replacing program files and attempts rollback if installation fails. User settings are stored separately and are not part of the update package.

## Русское описание

Подробное описание возможностей, сленга, оверлея и установки: **[README_RU.md](README_RU.md)**.

## Build from source on Windows

Requirements:

- Python 3.12+
- Inno Setup 6

Run:

```bat
BUILD_RELEASE.bat
```

The build runs tests, creates `CoD2ChatTranslator.exe`, `CoD2ChatTranslatorUpdater.exe`, the update ZIP/manifest, and the bilingual installer.

## Support the project

If the translator is useful to you, a ⭐ on this repository helps other Call of Duty 2 players find it.
