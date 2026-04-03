"""
PyX Wizard — Example 10: Advanced Pipeline
============================================
A production-grade build pipeline showing:

  1. Self-packaging mode  — build.py packages *itself*
  2. outlocation()        — store PyX_Data in a separate output directory
  3. extra_flags()        — pass raw PyInstaller flags (e.g. --onefile, UPX)
  4. feedback("finish")   — only print the final result box
  5. Multi-target loop    — build several apps in sequence, each with full
                            build result inspection and JSON persistence
  6. Purge on failure     — call purge() to fully remove a failed project dir

Usage:
    python pipeline.py [--dry-run]

Requirements:
    pip install pyxwizard

Notes:
    In self-packaging mode (target "self"), pyxwizard.location("self")
    packages the calling script (this file). All `import pyxwizard` and
    `pyxwizard.xxx()` lines are automatically stripped from the copy.
    Self-mode CANNOT be combined with data().
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import pyxwizard

# ── Argument parsing ──────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", help="Validate only, skip PyInstaller")
args = parser.parse_args()

# ── Build targets ─────────────────────────────────────────────────────────────

@dataclass
class BuildTarget:
    script: str          # path or "self"
    name: str
    console: bool = True
    version: Optional[str] = None
    extra_flags: tuple = ()
    data_folders: tuple = ()


TARGETS = [
    BuildTarget(
        script="tools/converter.py",
        name="FileConverter",
        console=True,
        version="2.0.0",
        extra_flags=("--onefile",),   # single-file EXE via PyInstaller flag
    ),
    BuildTarget(
        script="tools/monitor.py",
        name="SystemMonitor",
        console=False,
        version="1.3.2",
        data_folders=("tools/monitor_config",),
    ),
    BuildTarget(
        script="self",               # package this pipeline script itself
        name="BuildPipeline",
        console=True,
        version="10.0.0",
        extra_flags=("--clean",),    # force clean PyInstaller cache
    ),
]

# ── Pipeline configuration ────────────────────────────────────────────────────

OUTPUT_BASE = Path("pipeline_output")
OUTPUT_BASE.mkdir(exist_ok=True)

# Only print the final BUILD SUCCESSFUL / FAILED box per target
pyxwizard.feedback("finish")

results_summary = []

# ── Build loop ────────────────────────────────────────────────────────────────

for target in TARGETS:
    print(f"\n{'─'*55}")
    print(f"  Target: {target.name}  (script={target.script})")
    print(f"{'─'*55}")

    pyxwizard.begin()

    pyxwizard.location(target.script)
    pyxwizard.name(target.name)
    pyxwizard.console(target.console)
    pyxwizard.author("Pipeline v10")

    if target.version:
        pyxwizard.version(target.version)

    if target.extra_flags:
        pyxwizard.extra_flags(*target.extra_flags)

    if target.data_folders:
        pyxwizard.data(*target.data_folders)

    # Store each project's PyX_Data under the shared output directory
    pyxwizard.outlocation(str(OUTPUT_BASE))

    if args.dry_run:
        pyxwizard.dry_run(True)

    result = pyxwizard.build()

    # Persist individual result
    result_path = OUTPUT_BASE / f"{target.name}_build_result.json"
    result_path.write_text(result.to_json(), encoding="utf-8")

    entry = {
        "name":     target.name,
        "success":  result.success,
        "exe":      str(result.exe_path) if result.exe_path else None,
        "size_mb":  round(result.exe_size_mb, 2) if result.success else None,
        "duration": round(result.build_duration_seconds, 1),
        "version":  result.version_string,
        "signed":   result.signed,
        "error":    result.error_message,
    }
    results_summary.append(entry)

    if not result.success:
        print(f"  ⚠  Purging failed project directory for '{target.name}'…")
        pyxwizard.purge(target.name)

# ── Pipeline summary ──────────────────────────────────────────────────────────

summary_path = OUTPUT_BASE / "pipeline_summary.json"
summary_path.write_text(json.dumps(results_summary, indent=2), encoding="utf-8")

print(f"\n{'═'*55}")
print("  PIPELINE SUMMARY")
print(f"{'═'*55}")
for entry in results_summary:
    icon = "✅" if entry["success"] else "❌"
    size = f"{entry['size_mb']} MB" if entry["size_mb"] else "—"
    print(f"  {icon}  {entry['name']:<22}  {size:<10}  {entry['duration']}s")
print(f"{'═'*55}")
print(f"\nFull summary → {summary_path}")

failed = [e for e in results_summary if not e["success"]]
sys.exit(1 if failed else 0)
