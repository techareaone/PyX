# PyX Wizard — Example Collection

A structured set of examples covering every major feature of the
[PyX Wizard](https://pypi.org/project/pyxwizard/) library (v0.29.4+).

## Prerequisites

```bash
pip install pyxwizard
```

Python 3.9+ and Windows are required (EXE output is Windows-only).

---

## Examples at a glance

| # | Folder | What it covers |
|---|--------|----------------|
| 01 | `01_quickstart/` | Minimal build — `begin`, `location`, `name`, `build` |
| 02 | `02_gui_app/` | GUI app — `console(False)`, `icon`, `author` |
| 03 | `03_data_bundle/` | Bundled folders — `data()`, packaged-within-exe paths |
| 04 | `04_signed_build/` | Code signing — `cert(pfx, pwd, signtool)` |
| 05 | `05_splash_screen/` | Splash image — `splash(image, timeout)` |
| 06 | `06_versioned_build/` | Version metadata — `version(ver, desc)`, full `BuildResult` |
| 07 | `07_gui_builder/` | GUI integration — `feedback("none")`, `on_progress`, `on_log`, `on_step` |
| 08 | `08_dry_run/` | Dry run — `dry_run(True)`, `feedback("step")`, `step_results` |
| 09 | `09_post_build/` | Hooks & maintenance — `hook_pre`, `hook_post`, `report`, `snapshot`, `rebuild`, `clean` |
| 10 | `10_advanced_pipeline/` | Full pipeline — `outlocation`, `extra_flags`, self-mode, `purge`, multi-target loop |

---

## API coverage map

| API call | Example(s) |
|---|---|
| `begin()` | All |
| `location(path)` | All |
| `name(name)` | All |
| `author(name)` | 02, 04, 06 |
| `console(bool)` | 02, 03, 05, 06 |
| `icon(path)` | 02, 05 |
| `data(f1, f2, …)` | 03, 10 |
| `cert(pfx, pwd, signtool?)` | 04 |
| `version(ver, desc?)` | 06, 09, 10 |
| `splash(image, timeout?)` | 05 |
| `extra_flags(f1, f2, …)` | 10 |
| `outlocation(path)` | 10 |
| `dry_run(bool)` | 08 |
| `feedback(mode)` | 07, 08, 09, 10 |
| `on_progress(fn)` | 07 |
| `on_log(fn)` | 07 |
| `on_step(fn)` | 07 |
| `hook_pre(fn)` | 09 |
| `hook_post(fn)` | 09 |
| `build()` → `BuildResult` | All |
| `rebuild()` | 09 |
| `report()` | 09 |
| `snapshot()` | 09 |
| `clean(name?)` | 09 |
| `purge(name?)` | 10 |
| `get_steps()` | 09 |
| `get_version()` | 09 |
| `BuildResult.to_json()` | 08, 10 |
| `BuildResult.summary()` | 06 |
| `BuildResult.step_results` | 08 |
| `BuildResult.dependencies` | 03, 08 |

---

## Feedback modes

| Mode | Used in | Effect |
|---|---|---|
| `"full"` | (default) | Everything — banner, progress, all logs |
| `"step"` | 08, 09 | Step headers + final summary |
| `"finish"` | 10 | Final SUCCESSFUL/FAILED box only |
| `"none"` | 07 | Complete silence — use callbacks instead |

---

## Running any example

```bash
cd 01_quickstart
python build.py
```

Each folder has its own `README.md` with specific setup notes.

---

## Notes

- **Self-mode** (`pyxwizard.location("self")`) cannot be combined with `data()`.
- **Venv reuse**: building the same project name twice reuses the existing venv.
- **Callbacks** (`on_progress`, `on_log`, `on_step`) and `feedback()` persist
  across `begin()` calls — register them once.
- **Signing** (Example 04) requires a valid `.pfx` certificate and `signtool.exe`.
- **Splash screen** (Example 05) requires PyInstaller 4.6+ and tkinter.
