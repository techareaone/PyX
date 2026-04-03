"""
PyX Wizard — Example 08: Dry Run & Config Validation
======================================================
dry_run(True) runs every preparation step (virtual environment creation,
dependency installation, preprocessing) but stops before invoking
PyInstaller. Useful for:

  - CI pipelines: validate the build config without waiting for a full build
  - Debugging:    check dependencies and preprocessing without burning time
  - Testing:      confirm that all data files and hooks are wired correctly

BuildResult is still returned and populated with everything that ran.

Requirements:
    pip install pyxwizard

Usage:
    python build.py
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import json
import pyxwizard

pyxwizard.feedback("step")   # show step headers but not every log line

pyxwizard.begin()

pyxwizard.location("complex_app.py")
pyxwizard.name("ComplexApp")
pyxwizard.console(False)
pyxwizard.version("0.1.0-beta")
pyxwizard.data("config", "templates")

# Skip the actual PyInstaller compilation
pyxwizard.dry_run(True)

result = pyxwizard.build()

print("\n─── Dry Run Report ───")
print(f"Success     : {result.success}")
print(f"Project dir : {result.project_dir}")
print(f"Script hash : {result.script_hash}")
print(f"Log dir     : {result.log_dir}")

# Inspect each build step
print("\nStep timings:")
if result.step_results:
    for step in result.step_results:
        status = "✓" if step.success else "✗"
        print(f"  {status}  {step.step_id:<30}  {step.duration_seconds:.2f}s")

# Inspect bundled dependencies
print(f"\nDependencies detected ({len(result.dependencies)}):")
for dep in result.dependencies[:10]:   # show first 10
    print(f"  [{dep.status:>8}]  {dep.name}  ({dep.category})")

# Serialise full result for CI artefact upload
result_json = result.to_json()
with open("dry_run_result.json", "w") as f:
    f.write(result_json)
print("\nFull result saved to dry_run_result.json")
