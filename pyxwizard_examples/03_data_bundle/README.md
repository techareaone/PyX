# Example 03 — Bundling Data Folders

**What it shows:** Packing extra folders (config, assets, databases) into the EXE
and reading them at runtime using PyX Wizard's special path strings.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `data_reader_app.py` | App that reads bundled files |
| `config/settings.json` | JSON config — bundled into EXE |
| `assets/motd.txt` | Text asset — bundled into EXE |

## How bundled paths work
In your source code, reference bundled files with:
```python
open("packaged-within-exe:config/settings.json")
```
PyX Wizard's preprocessor rewrites these strings automatically at build time
so the file resolves correctly both from source *and* inside the packaged EXE.

## Key API call
```python
pyxwizard.data("config", "assets")   # pass as many folder names as needed
```

## ⚠️ Restriction
`pyxwizard.location("self")` **cannot** be combined with `pyxwizard.data(...)`.
Always pass an explicit script path when bundling folders.
