# PyX Wizard — Library Edition v0.29.2

**Python → EXE Builder**  
Package Python scripts into standalone Windows executables from code.

## Quick Start

```python
import pyxwizard

pyxwizard.begin()
pyxwizard.location("my_script.py")
pyxwizard.name("MyApp")
pyxwizard.build()
```

## API Reference

| Command | Required | Default | Description |
|---|---|---|---|
| `pyxwizard.begin()` | Yes | — | Initialise PyX Wizard, fetch library categories |
| `pyxwizard.location(path)` | Yes | — | Script path or `"self"` (`"self"` does not work with Data Folders) |
| `pyxwizard.name(name)` | Yes | — | Project name (= EXE filename) |
| `pyxwizard.author(name)` | No | `"TRADELY.DEV"` | Author metadata |
| `pyxwizard.console(bool)` | No | `True` | Show console window |
| `pyxwizard.icon(path)` | No | Tradely icon | Custom `.ico` file |
| `pyxwizard.data(f1, f2, ...)` | No | None | Folders to bundle |
| `pyxwizard.cert(pfx, pwd, signtool?)` | No | None | Code signing cert (PFX/P12) |
| `pyxwizard.outlocation(path)` | No | Script dir | Where to put `PyX_Data/` |
| `pyxwizard.build()` | Yes | — | Run the build, returns `BuildResult` |
| `pyxwizard.version(ver, desc?)` | No | None | Embed version in EXE file properties |
| `pyxwizard.splash(image, timeout?)` | No | None | Splash screen on EXE startup |
| `pyxwizard.extra_flags(f1, f2, ...)` | No | None | Pass extra flags to PyInstaller |
| `pyxwizard.hook_pre(fn)` | No | None | Run a function before PyInstaller |
| `pyxwizard.hook_post(fn)` | No | None | Run a function after build (gets `BuildResult`) |
| `pyxwizard.dry_run(bool)` | No | `False` | Validate everything but skip PyInstaller |
| `pyxwizard.feedback(mode)` | No | `"full"` | Control terminal output level (see below) |

## Feedback Modes

Control how much terminal output PyX Wizard produces during a build.

```python
import pyxwizard

pyxwizard.feedback("step")   # Only show step headers + final result
pyxwizard.begin()
pyxwizard.location("my_script.py")
pyxwizard.name("MyApp")
pyxwizard.build()
```

| Mode | What prints | Best for |
|---|---|---|
| `"full"` | Everything — banner, step headers, progress bars, every log line, final summary | Terminal / debugging |
| `"step"` | Step headers (e.g. `VIRTUAL ENVIRONMENT`, `PYINSTALLER BUILD`) + final summary | Cleaner terminal view |
| `"finish"` | Only the final `BUILD SUCCESSFUL` or `BUILD FAILED` box with summary stats | Background builds |
| `"none"` | Nothing at all — complete silence | GUI apps (use callbacks instead) |

> **Note:** Callbacks (`on_progress`, `on_log`, `on_step`) always fire regardless of feedback mode. Set `feedback("none")` and wire up callbacks to fully control output from your own GUI.

## GUI Integration — Callbacks

Wire PyX Wizard directly into your GUI without any terminal noise.

```python
import pyxwizard

# Suppress all terminal output
pyxwizard.feedback("none")

# Wire your widgets
pyxwizard.on_progress(my_progress_bar.set)    # fn(value: 0.0–1.0, label: str)
pyxwizard.on_log(my_textbox.append)           # fn(message: str)
pyxwizard.on_step(my_sidebar.update)          # fn(step_id: str, label: str, progress: float)

pyxwizard.begin()
pyxwizard.location("my_script.py")
pyxwizard.name("MyApp")
result = pyxwizard.build()
```

| Command | Required | Default | Description |
|---|---|---|---|
| `pyxwizard.on_progress(fn)` | No | None | `fn(value, label)` — fires at every progress update |
| `pyxwizard.on_log(fn)` | No | None | `fn(message)` — fires for every log line |
| `pyxwizard.on_step(fn)` | No | None | `fn(step_id, label, progress)` — fires when a build step starts |

## BuildResult

`pyxwizard.build()` returns a `BuildResult` object with everything you need.

```python
result = pyxwizard.build()

if result.success:
    print(f"EXE: {result.exe_path}")
    print(f"Size: {result.exe_size_mb:.1f} MB")
    print(f"Time: {result.build_duration_seconds:.1f}s")
else:
    print(f"Failed: {result.error_message}")
```

| Property | Type | Description |
|---|---|---|
| `.success` | `bool` | Whether the build succeeded |
| `.exe_path` | `Path` | Path to the built executable (`None` on failure) |
| `.exe_size_mb` | `float` | EXE file size in megabytes |
| `.exe_size_bytes` | `int` | EXE file size in bytes |
| `.signed` | `bool` | Whether the EXE was code-signed |
| `.build_duration_seconds` | `float` | Total build time |
| `.project_dir` | `Path` | Path to `PyX_Data/<project>/` |
| `.dist_dir` | `Path` | Path to `PyX_Data/<project>/dist/` |
| `.log_dir` | `Path` | Path to `PyX_Data/<project>/logs/` |
| `.manifest_path` | `Path` | Path to `pyx_manifest.json` |
| `.report_path` | `Path` | Path to `dependency_report.txt` |
| `.dependencies` | `list` | List of `DependencyInfo` (name, category, status) |
| `.step_results` | `list` | List of `StepResult` (per-step success, timing) |
| `.error_message` | `str` | Error description (`None` on success) |
| `.error_traceback` | `str` | Full traceback (`None` on success) |
| `.log_lines` | `list` | All log messages as a list of strings |
| `.script_hash` | `str` | SHA-256 hash of the source script |
| `.version_string` | `str` | Embedded version (`None` if not set) |
| `.icon_used` | `str` | Path to the icon that was used |
| `.python_version` | `str` | Python version used for the build |
| `.platform_info` | `str` | OS and architecture |
| `.pyx_version` | `str` | PyX Wizard library version |
| `.to_json()` | `str` | Serialise the full result to JSON |
| `.to_dict()` | `dict` | Serialise the full result to a dictionary |
| `.summary()` | `str` | Human-readable multi-line summary |

## Post-Build & Maintenance

| Command | Required | Default | Description |
|---|---|---|---|
| `pyxwizard.report()` | No | — | Print and return the dependency report |
| `pyxwizard.snapshot()` | No | — | Return the environment snapshot as a dict |
| `pyxwizard.clean(name?)` | No | Current project | Remove `build/` and `dist/`, keep venv & logs |
| `pyxwizard.purge(name?)` | No | Current project | Delete the entire project directory |
| `pyxwizard.rebuild()` | No | — | Re-run the build with the current config |
| `pyxwizard.get_steps()` | No | — | List all build step IDs, labels, and progress values |
| `pyxwizard.get_version()` | No | — | Return the library version string |

## Output Files

Every build produces the following files inside `PyX_Data/<project>/`:

| File | Location | Description |
|---|---|---|
| `<project>.exe` | `dist/` | The built executable |
| `pyx_manifest.json` | root | Build config and metadata |
| `build_result.json` | root | Full `BuildResult` as JSON |
| `dependency_report.txt` | root | Dependency table with install status |
| `environment_snapshot.json` | root | pip freeze + platform info |
| `build_YYYYMMDD_HHMMSS.txt` | `logs/` | Timestamped build log |

---

## Notes

- **"self" mode**: `pyxwizard.location("self")` packages the calling script. All `import pyxwizard` and `pyxwizard.xxx()` lines are automatically removed from the packaged copy.

- **Data folders**: Files in bundled folders are accessible at runtime with `"packaged-within-exe:folder_name/file.ext"` string literals (auto-rewritten by the preprocessor). Exclusion: `pyxwizard.location("self")` cannot be used with Data Folders.

- **Venv reuse**: Building the same project name twice reuses the existing virtual environment instead of recreating it.

- **Library categories**: On `begin()`, PyX Wizard fetches a remote JSON of known library metadata to improve PyInstaller compatibility (collect-all, hidden-imports, copy-metadata). Works offline too — just without categorisation.

- **Version info**: `pyxwizard.version("1.2.3")` embeds file properties visible in Windows Explorer → right-click → Properties → Details tab.

- **Splash screen**: `pyxwizard.splash("splash.png")` requires PyInstaller 4.6+ and Tkinter available in the target environment.

- **Dry run**: `pyxwizard.dry_run(True)` runs every step (venv, deps, preprocessing) except the actual PyInstaller build — useful for validating your config.

## Further Details

Check out [PyX Wizard by TRADELY](https://doc.tradely.dev)

PyPI Library available at: [PyPI PyXWizard](https://pypi.org/project/PyXWizard/)

Use the README there to set up the library.
