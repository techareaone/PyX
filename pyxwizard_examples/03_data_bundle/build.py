"""
PyX Wizard — Example 03: Bundling Data Folders
================================================
Shows how to bundle extra folders (config files, assets, databases, etc.)
into the EXE so they are available at runtime.

The packaged app reads files using the special path string
"packaged-within-exe:folder_name/file.ext" which PyX Wizard's
preprocessor rewrites automatically.

Requirements:
    pip install pyxwizard

Usage:
    python build.py

Important:
    pyxwizard.location("self") CANNOT be used when bundling data folders.
    Always specify an explicit script path.
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import pyxwizard

pyxwizard.begin()

pyxwizard.location("data_reader_app.py")
pyxwizard.name("DataReaderApp")

# Bundle two folders into the EXE
# They will be accessible inside the app via the special path string
pyxwizard.data("config", "assets")

pyxwizard.console(True)   # keep console so we can see output

result = pyxwizard.build()

if result:
    print(f"✅ Built: {result.exe_path}")
    print(f"   Dependencies bundled: {len(result.dependencies)}")
else:
    print(f"❌ Error: {result.error_message}")
    if result.error_traceback:
        print(result.error_traceback)
