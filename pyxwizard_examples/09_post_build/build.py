"""
PyX Wizard — Example 09: Post-Build Hooks & Maintenance
=========================================================
Demonstrates:
  - hook_pre(fn)   : run custom logic before PyInstaller (e.g. inject build number)
  - hook_post(fn)  : run custom logic after the build (e.g. copy EXE to a release folder)
  - report()       : print/return the dependency table
  - snapshot()     : return the full environment snapshot dict
  - rebuild()      : re-run the last build with no reconfiguration
  - clean()        : remove build/ and dist/ while keeping venv and logs
  - get_steps()    : list all build step IDs and progress weights
  - get_version()  : return PyX Wizard library version string

Requirements:
    pip install pyxwizard

Usage:
    python build.py
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import shutil
import datetime
from pathlib import Path

import pyxwizard

RELEASE_DIR = Path("release")


# ── Pre-build hook ────────────────────────────────────────────────────────────

def inject_build_metadata() -> None:
    """
    Called by PyX Wizard just before PyInstaller runs.
    Here we write a build_info.py file that the app can import to display
    its build timestamp and number at runtime.
    """
    build_info_path = Path("build_info.py")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    build_info_path.write_text(
        f'BUILD_TIMESTAMP = "{timestamp}"\n'
        f'BUILD_NUMBER    = 42\n'
        f'BUILT_BY        = "PyX Wizard automated pipeline"\n',
        encoding="utf-8",
    )
    print(f"  [pre-hook] Wrote {build_info_path} with timestamp {timestamp}")


# ── Post-build hook ───────────────────────────────────────────────────────────

def copy_to_release(result) -> None:
    """
    Called by PyX Wizard after a successful build with the BuildResult.
    Copies the finished EXE to a versioned release folder.
    """
    if not result.success:
        print("  [post-hook] Build failed — skipping release copy.")
        return

    RELEASE_DIR.mkdir(exist_ok=True)
    dest = RELEASE_DIR / result.exe_path.name
    shutil.copy2(result.exe_path, dest)
    print(f"  [post-hook] Copied EXE → {dest}")

    # Also save the JSON report
    report_dest = RELEASE_DIR / "build_result.json"
    report_dest.write_text(result.to_json(), encoding="utf-8")
    print(f"  [post-hook] Saved build result → {report_dest}")


# ── Build configuration ───────────────────────────────────────────────────────

pyxwizard.feedback("step")

pyxwizard.begin()

pyxwizard.location("info_app.py")
pyxwizard.name("InfoApp")
pyxwizard.console(True)
pyxwizard.version("1.0.0")
pyxwizard.author("Pipeline Bot")

# Register hooks
pyxwizard.hook_pre(inject_build_metadata)
pyxwizard.hook_post(copy_to_release)

# ── First build ───────────────────────────────────────────────────────────────

print(f"\nPyX Wizard version: {pyxwizard.get_version()}\n")

print("Available build steps:")
for step in pyxwizard.get_steps():
    print(f"  {step['id']:<35} weight={step['progress']:.2f}  ({step['label']})")

print()

result = pyxwizard.build()

if result:
    print(f"\n✅  Build 1 complete: {result.exe_path}")

    # Print the dependency report
    print("\n── Dependency Report ──")
    pyxwizard.report()

    # Inspect environment snapshot
    snap = pyxwizard.snapshot()
    print(f"\nEnvironment snapshot keys: {list(snap.keys())}")

    # ── Rebuild (reuses venv, re-runs PyInstaller) ─────────────────────────
    print("\n── Rebuilding (venv reused)… ──")
    result2 = pyxwizard.rebuild()
    if result2:
        print(f"✅  Rebuild complete: {result2.exe_path}")

    # ── Clean (removes build/ and dist/, keeps venv and logs) ─────────────
    print("\n── Cleaning build artefacts… ──")
    pyxwizard.clean()
    print("   build/ and dist/ removed. venv and logs retained.")

else:
    print(f"\n❌  {result.error_message}")
    if result.error_traceback:
        print(result.error_traceback)
