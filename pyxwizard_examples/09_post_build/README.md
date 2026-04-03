# Example 09 — Post-Build Hooks & Maintenance

**What it shows:** Using pre/post hooks to inject build metadata and copy
the finished EXE to a release folder, plus the full maintenance API
(`report`, `snapshot`, `rebuild`, `clean`, `get_steps`, `get_version`).

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `info_app.py` | App that displays build metadata at runtime |
| `build_info.py` | *(generated)* Written by the pre-build hook |
| `release/` | *(generated)* EXE copied here by the post-build hook |

## Hook API
```python
# Pre-hook — called before PyInstaller, no arguments
pyxwizard.hook_pre(fn)

# Post-hook — called after build, receives BuildResult
pyxwizard.hook_post(fn)   # fn(result: BuildResult)
```

## Maintenance API demonstrated
| Call | Effect |
|---|---|
| `pyxwizard.report()` | Print + return the dependency table |
| `pyxwizard.snapshot()` | Return env snapshot dict (pip freeze + platform) |
| `pyxwizard.rebuild()` | Re-run build with current config, venv reused |
| `pyxwizard.clean()` | Remove `build/` and `dist/`, keep venv + logs |
| `pyxwizard.get_steps()` | List all step IDs, labels, progress weights |
| `pyxwizard.get_version()` | PyX Wizard library version string |
