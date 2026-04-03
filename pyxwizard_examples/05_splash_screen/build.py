"""
PyX Wizard — Example 05: Splash Screen
========================================
Adds a branded splash image that displays while the EXE loads.
PyX Wizard (v0.29.4+) automatically installs Pillow in the build
venv and validates tkinter availability — if tkinter is missing
the splash is skipped with a warning rather than failing the build.

Requirements:
    pip install pyxwizard
    PyInstaller 4.6+

Usage:
    python build.py

Notes:
    - Place a PNG/JPG at assets/splash.png (recommended: 600×400 px).
    - timeout is how many seconds the splash stays visible (default: auto).
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import pyxwizard

pyxwizard.begin()

pyxwizard.location("heavy_app.py")
pyxwizard.name("HeavyApp")
pyxwizard.console(False)
pyxwizard.icon("assets/app.ico")
pyxwizard.version("1.0.0")

# Show splash.png for up to 5 seconds while the app loads
pyxwizard.splash("assets/splash.png", timeout=5)

result = pyxwizard.build()

if result:
    print(f"✅  Built: {result.exe_path}  ({result.exe_size_mb:.1f} MB)")
else:
    print(f"❌  {result.error_message}")
