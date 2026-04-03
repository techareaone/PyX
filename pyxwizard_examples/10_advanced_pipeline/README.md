# Example 10 — Advanced Pipeline

**What it shows:** A production-grade multi-target build pipeline combining
self-packaging, custom output locations, extra PyInstaller flags, and
automated cleanup on failure.

## Files
| File | Purpose |
|---|---|
| `pipeline.py` | Main pipeline script |
| `tools/converter.py` | File converter — built as `--onefile` |
| `tools/monitor.py` | System monitor GUI — built with bundled config |
| `tools/monitor_config/config.json` | Config bundled into the monitor EXE |
| `pipeline_output/` | *(generated)* All build artefacts and JSON reports |

## Running
```bash
# Full build
python pipeline.py

# Validation only (skip PyInstaller)
python pipeline.py --dry-run
```

## Features demonstrated

### Self-packaging
```python
pyxwizard.location("self")   # packages pipeline.py itself
```
All `import pyxwizard` and `pyxwizard.xxx()` lines are automatically
stripped from the packaged copy.

### Custom output location
```python
pyxwizard.outlocation("pipeline_output")
```
All `PyX_Data/` directories are written under `pipeline_output/` instead
of the script directory.

### Extra PyInstaller flags
```python
pyxwizard.extra_flags("--onefile")     # single-file EXE
pyxwizard.extra_flags("--clean")       # force clean cache
```

### Feedback mode
```python
pyxwizard.feedback("finish")   # only show final SUCCESSFUL/FAILED box
```

### Purge on failure
```python
if not result.success:
    pyxwizard.purge(target.name)   # delete entire project directory
```

### Exit code
The pipeline exits with code `1` if any target failed — compatible with
CI systems (GitHub Actions, GitLab CI, Jenkins, etc.).
