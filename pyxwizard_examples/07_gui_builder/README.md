# Example 07 — GUI Builder with Live Callbacks

**What it shows:** Embedding PyX Wizard inside a tkinter GUI application.
All terminal output is suppressed; instead, a progress bar, live log box,
and step indicator are driven entirely by PyX Wizard's callback API.

## Files
| File | Purpose |
|---|---|
| `gui_builder.py` | Full GUI builder — run this directly |

## Running
```
pip install pyxwizard
python gui_builder.py
```
Browse to any `.py` script, give it a name, and click **BUILD**.

## Callback API used
```python
pyxwizard.feedback("none")           # silence all terminal output
pyxwizard.on_progress(fn)            # fn(value: float 0–1, label: str)
pyxwizard.on_log(fn)                 # fn(message: str)
pyxwizard.on_step(fn)                # fn(step_id: str, label: str, progress: float)
```

## Key design patterns
- Callbacks and `feedback()` are registered **before** `begin()` and persist
  across multiple `begin()` calls — wire them up once.
- `pyxwizard.build()` is run on a **background thread** to keep the GUI
  responsive during the build.
- The build result is marshalled back to the main thread via `root.after(0, ...)`.
