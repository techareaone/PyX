# Example 06 — Version Embedding

**What it shows:** Embedding version metadata into the EXE file properties and
inspecting the full `BuildResult` object after a successful build.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `inventory_app.py` | GUI inventory manager being packaged |

## Viewing embedded version info
After building, right-click `InventoryManager.exe` in Windows Explorer →
**Properties** → **Details** tab. You will see the version and description
you passed to `pyxwizard.version()`.

## Key API call
```python
pyxwizard.version("3.1.4", "Inventory Manager — tracks stock levels and orders")
```

## BuildResult properties demonstrated
```python
result.version_string   # "3.1.4"
result.python_version   # e.g. "3.11.8"
result.platform_info    # e.g. "Windows-11-AMD64"
result.pyx_version      # PyX Wizard library version
result.script_hash      # SHA-256 of the source script
result.summary()        # human-readable multi-line summary
```
