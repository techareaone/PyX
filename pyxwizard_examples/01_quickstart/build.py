"""
PyX Wizard — Example 01: Quick Start
=====================================
The simplest possible build. Takes a Python script and packages it
into a standalone Windows EXE with minimal configuration.

Requirements:
    pip install pyxwizard

Usage:
    python build.py
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory
import pyxwizard

# 1. Initialise PyX Wizard (fetches remote library metadata)
pyxwizard.begin()

# 2. Point at the script to package
pyxwizard.location("hello_world.py")

# 3. Set the output EXE name
pyxwizard.name("HelloWorld")

# 4. Build!
result = pyxwizard.build()

if result:
    print(f"✅ Success! EXE at: {result.exe_path}")
    print(f"   Size : {result.exe_size_mb:.1f} MB")
    print(f"   Time : {result.build_duration_seconds:.1f}s")
else:
    print(f"❌ Build failed: {result.error_message}")
