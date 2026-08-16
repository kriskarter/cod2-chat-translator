# CoD2 Chat Translator v1.11.1 — build status

## VERIFIED in this environment

- `APP_VERSION = 1.11.1`.
- Python compile and unit tests.
- Update manifest/version comparison tests.
- Updater archive traversal protection and SHA256 logic preserved.
- Installer resources use the COD 2 icon.
- Installer side-art text corrected to `translation`.
- User settings remain outside the install directory.

## IMPLEMENTED_NOT_VERIFIED ON WINDOWS HERE

- PyInstaller Windows EXE compilation.
- Inno Setup `CoD2ChatTranslator_Setup_v1.11.1.exe`.
- End-to-end live update from a GitHub Release, because the dedicated public repository has not been created yet.

## NEXT RELEASE PIPELINE STEP

Create/publish `kriskarter/cod2-chat-translator`, push this source, then tag `v1.11.1`. GitHub Actions will build the installer and publish `update.json` + update ZIP. Existing installed clients configured to that repository will then receive future updates in one click.
