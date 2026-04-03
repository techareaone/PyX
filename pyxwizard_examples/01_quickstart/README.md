# Example 01 — Quick Start

**What it shows:** The absolute minimum needed to produce a working EXE.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `hello_world.py` | The script being packaged |

## Steps
1. `pip install pyxwizard`
2. `python build.py`
3. Find `HelloWorld.exe` inside `PyX_Data/HelloWorld/dist/`

## Key API calls
```python
pyxwizard.begin()
pyxwizard.location("hello_world.py")
pyxwizard.name("HelloWorld")
pyxwizard.build()
```
