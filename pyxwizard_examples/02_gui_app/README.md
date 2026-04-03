# Example 02 — GUI Application Build

**What it shows:** Packaging a tkinter GUI — hiding the console, adding a custom
icon, and embedding author metadata.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `calculator_app.py` | tkinter calculator being packaged |
| `assets/calculator.ico` | *(supply your own .ico)* Custom window icon |

## Providing an icon
Drop any `.ico` file at `assets/calculator.ico`, or remove the
`pyxwizard.icon()` line to use the default icon.

## Key API calls
```python
pyxwizard.console(False)          # hide black console window
pyxwizard.icon("assets/calculator.ico")
pyxwizard.author("My Company Ltd")
```
