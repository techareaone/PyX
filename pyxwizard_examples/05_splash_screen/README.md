# Example 05 — Splash Screen

**What it shows:** Displaying a branded image while a slow-starting EXE loads.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `heavy_app.py` | App that simulates slow startup |
| `assets/splash.png` | *(supply your own)* Splash image (PNG/JPG, ~600×400 px) |
| `assets/app.ico` | *(supply your own)* Window icon |

## Key API call
```python
pyxwizard.splash("assets/splash.png", timeout=5)
```
`timeout` (seconds) is optional. If omitted PyX Wizard picks a sensible default.

## Requirements
- PyInstaller 4.6 or newer
- tkinter available in your Python environment

## v0.29.4 behaviour
Pillow is **automatically installed** in the build venv if needed.  
If tkinter is unavailable the splash flag is **silently skipped** (warning printed)
instead of failing the entire build.
