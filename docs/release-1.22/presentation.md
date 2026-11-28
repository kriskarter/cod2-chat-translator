# GitHub presentation

**Description** — Translate Call of Duty 2 multiplayer chat on Windows, customize the F8 and F9 overlays, and track servers and friends.

**Topics** — call-of-duty-2, game-overlay, chat-translation, server-monitor, windows, pyside6.

**Social preview** — In repository Settings → General → Social preview, choose Edit and upload the [1280 × 640 image](../images/stable_release/common/social-preview.jpg). The image uses the running application with an empty server list.

**Release assets** — Attach the installer, SHA256SUMS.txt and the six localized installer captures. Fill the SHA-256 in all three release texts from the verified final binary. For the stable channel, generate installer-update.json with version, asset, sha256 and notes_en/notes_ru/notes_uk, then sign it using the existing tools/sign_update.py workflow secret. The installed client checks both the signed digest and the checksum file before launching the installer. Keep the preview and released legacy stable profiles available for rollback.
