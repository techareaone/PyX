# Example 08 — Dry Run & Config Validation

**What it shows:** Running all build preparation steps without invoking
PyInstaller — useful for CI validation, dependency auditing, and fast
config iteration.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script (dry run) |
| `complex_app.py` | Script with several dependencies to detect |
| `config/settings.json` | Bundled config folder |
| `templates/report.html` | Bundled templates folder |
| `dry_run_result.json` | Generated output — full build result as JSON |

## Key API call
```python
pyxwizard.dry_run(True)
```

## What runs during a dry run
| Step | Runs? |
|---|---|
| Virtual environment creation | ✅ |
| Dependency installation | ✅ |
| Script preprocessing | ✅ |
| PyInstaller compilation | ❌ skipped |

## CI usage pattern
```yaml
# GitHub Actions example
- name: Validate build config
  run: python build.py

- name: Upload dry run report
  uses: actions/upload-artifact@v3
  with:
    name: dry-run-result
    path: dry_run_result.json
```

## Feedback mode used
`pyxwizard.feedback("step")` — shows step headers and final summary,
hides individual log lines for a cleaner CI output.
