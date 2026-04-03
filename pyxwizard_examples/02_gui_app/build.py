"""
PyX Wizard — Example 02: GUI Application Build
================================================
Packaging a tkinter GUI app. Hides the console window, sets
a custom icon, and adds author metadata.

Requirements:
    pip install pyxwizard

Usage:
    python build.py

Notes:
    - Place your .ico file next to this script (or adjust the path).
    - If you don't have an icon, remove the pyxwizard.icon() call and
      PyX Wizard will use its default Tradely icon.
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import pyxwizard

pyxwizard.begin()

pyxwizard.location("calculator_app.py")
pyxwizard.name("Calculator")

# Hide the black console window — important for GUI apps
pyxwizard.console(False)

# Embed a custom icon into the EXE
pyxwizard.icon("assets/calculator.ico")

# Author metadata embedded in EXE file properties
pyxwizard.author("My Company Ltd")

result = pyxwizard.build()

if result:
    print(f"✅ GUI EXE built: {result.exe_path}")
    print(f"   Icon used : {result.icon_used}")
    print(f"   Signed    : {result.signed}")
else:
    print(f"❌ Failed: {result.error_message}")
