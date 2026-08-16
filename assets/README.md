# Branding assets

`source_icon.b64` contains the canonical COD 2 Chat Translator icon as base64-encoded PNG so the repository remains uploadable through text-only tooling.

Run:

```bash
python tools/build_assets.py
```

This reconstructs `source_icon.png` and generates the Windows `.ico`, runtime icon sizes and Inno Setup wizard BMP artwork. Generated files are ignored by Git.
