"""
PyX Wizard — Example 06: Version Embedding
============================================
Embeds version information into the EXE so it appears in Windows
Explorer → right-click → Properties → Details.

Shows how to use BuildResult to inspect what was embedded.

Requirements:
    pip install pyxwizard

Usage:
    python build.py
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import pyxwizard

APP_VERSION = "3.1.4"
APP_DESCRIPTION = "Inventory Manager — tracks stock levels and orders"

pyxwizard.begin()

pyxwizard.location("inventory_app.py")
pyxwizard.name("InventoryManager")
pyxwizard.console(False)
pyxwizard.author("Warehouse Solutions Inc.")

# Embed version info — visible in Windows Explorer file properties
pyxwizard.version(APP_VERSION, APP_DESCRIPTION)

result = pyxwizard.build()

if result:
    print("✅  Build successful")
    print(f"    EXE            : {result.exe_path}")
    print(f"    Version string : {result.version_string}")
    print(f"    Python used    : {result.python_version}")
    print(f"    Platform       : {result.platform_info}")
    print(f"    PyX version    : {result.pyx_version}")
    print(f"    Script hash    : {result.script_hash[:16]}...")
    print()
    # Full human-readable summary
    print(result.summary())
else:
    print(f"❌  {result.error_message}")
