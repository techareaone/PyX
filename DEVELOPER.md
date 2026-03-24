# PyX — Developer Reference

> Internal technical documentation for contributors and maintainers.

---

## Architecture

PyX is a single-file Python application (`PyX_V0_28_BETA.py`) built on `customtkinter`. The application is a multi-step wizard whose state flows through a shared `data` dictionary on the root `Wizard` instance. Each step is a `ctk.CTkFrame` subclass that reads from and writes to `wizard.data` before handing off navigation to the next step.

```
Wizard (ctk.CTk)
├── Sidebar (ctk.CTkFrame)
│   └── Step indicators, project count, output path, lib status
└── content_frame (ctk.CTkFrame)
    ├── StepWelcome   [index 0]
    ├── StepScript    [index 1]
    ├── StepConfig    [index 2]
    ├── StepData      [index 3]
    ├── StepCertificate [index 4]
    └── StepBuild     [index 5]
```

Navigation is handled by `Wizard.go_to_step(index)`, which hides the current frame and grids the target frame. Step frames are all instantiated at startup and kept in memory for the lifetime of the application.

---

## Shared State (`wizard.data`)

All cross-step data is stored in a single `dict` on the `Wizard` instance:

| Key | Type | Set by | Description |
|-----|------|--------|-------------|
| `script_path` | `Path \| None` | `StepScript` | Absolute path to the selected `.py` file. |
| `detected_imports` | `List[str]` | `StepScript` | Third-party imports found by AST scan. |
| `project_name` | `str` | `StepConfig` | Sanitised project name (used as folder and exe name). |
| `console_mode` | `bool` | `StepConfig` | If `False`, `--noconsole` is passed to PyInstaller. |
| `icon_path` | `str \| None` | `StepConfig` | Path to a `.ico` file, or `None` to use the default. |
| `data_folders` | `List[Path]` | `StepData` | Folders to bundle via `--add-data`. |
| `pfx_path` | `Path \| None` | `StepCertificate` | Path to the PFX certificate, or `None`. |
| `pfx_password` | `str \| None` | `StepCertificate` | Certificate password. |

---

## Key Modules and Functions

### `detect_script_imports(script_path: Path) → List[str]`

Parses the target script using `ast.parse()` and walks the AST to collect all `Import` and `ImportFrom` nodes. Rules applied:

- Only the top-level package name is kept (`os.path` → `os`).
- Standard library modules defined in `_STDLIB_SKIP` are excluded.
- `pyinstaller` is explicitly excluded to prevent it being passed as a hidden import.
- Only valid Python identifiers are retained.

Returns a sorted, deduplicated list.

---

### `preprocess_script(script_path, temp_dir, data_folders, console_mode) → Path`

Writes a modified copy of the target script to `temp_dir`. The preprocessing pipeline:

1. Reads the source as UTF-8.
2. Strips any existing `if __name__ == "__main__":` guard (PyInstaller requires the entry point to be at module level).
3. Removes `multiprocessing.freeze_support()` calls (PyX handles this itself).
4. Injects `INJECTED_PATH_HELPER` immediately after the last `import` statement if not already present.
5. Rewrites all `"packaged-within-exe:<relpath>"` string literals to `_resolve_packaged_path("<relpath>")` calls using a regex substitution.

The preprocessed file is what gets passed to PyInstaller, not the original.

---

### `INJECTED_PATH_HELPER`

A string constant containing a small Python snippet that is injected into every target script. It provides:

- `_resolve_packaged_path(relative_path: str) → str` — resolves resource paths against `sys._MEIPASS` when frozen, or `__file__` when running as a script.
- A `os.chdir()` call that sets the working directory to the executable location when frozen, so paths relative to the exe work as expected.

This injection is idempotent; the presence check `"# --- PyX Wizard: injected path helper (start) ---"` prevents double-injection on rebuild.

---

### `_fetch_lib_categories() → bool`

Downloads `LIBRARIES_CATEGORY_FILE` on a daemon thread at startup and populates four module-level globals:

| Global | Type | Purpose |
|--------|------|---------|
| `_lib_categories` | `Dict[str, str]` | Maps lowercase lib name → category label for UI display. |
| `_lib_collect_all` | `Set[str]` | Packages that need `--collect-all` in PyInstaller. |
| `_lib_hidden_imports` | `Dict[str, List[str]]` | Per-package additional `--hidden-import` values. |
| `_lib_copy_metadata` | `Dict[str, str]` | Import name → pip distribution name for `--copy-metadata`. |

Expected JSON schema:

```json
{
  "collect_all": ["OpenGL", "sklearn"],
  "hidden_imports": {
    "sklearn": ["sklearn.utils._cython_blas"]
  },
  "copy_metadata": {
    "sklearn": "scikit-learn"
  },
  "categories": {
    "Data Science": ["numpy", "pandas", "sklearn"],
    "Web": ["requests", "flask"]
  }
}
```

The fetch happens on a daemon thread. The UI globe indicator is updated via `Wizard.after()` to stay thread-safe.

---

### `create_project_venv(project_dir, log) → Path`

Creates a virtual environment under `project_dir/venv/` using `venv.create()`. When PyX is running as a frozen executable, `sys.executable` is the packaged binary rather than a Python interpreter, so `shutil.which("python")` is used to locate the system interpreter and `subprocess` is used to invoke it directly.

Returns the path to the venv Python executable.

---

### Build Worker (`StepBuild._build_worker`)

Runs on a daemon thread started by `_start_build()`. The full sequence:

```
1.  Create project directory tree (venv/, build/, dist/, logs/)
2.  Create or reuse virtual environment
3.  Upgrade pip
4.  Install PyInstaller into the venv
5.  Detect and install script dependencies
6.  Download default icon if none provided
7.  Preprocess the target script to a temp directory
8.  Construct and run the PyInstaller command
9.  Locate the output executable in dist/
10. Optionally sign the executable
11. Write pyx_manifest.json
12. Write timestamped build log
```

All GUI updates from the worker are dispatched via `self.after(0, ...)` to maintain thread safety. On both success and failure, the temp directory is cleaned up in a `finally` block.

---

### PyInstaller Command Construction

The command is assembled incrementally in the build worker:

```python
[python_exe, "-m", "PyInstaller",
 "--onefile", "--clean", "--noconfirm",
 "--name", project_name,
 "--distpath", dist_dir,
 "--workpath", build_dir,
 # Conditional flags:
 "--noconsole",                        # if not console_mode
 "--icon", icon_path,                  # if icon provided
 "--hidden-import", name,              # per detected import
 "--collect-all", pkg,                 # for packages in _COLLECT_ALL_PACKAGES
 "--hidden-import", hi,                # from _lib_hidden_imports
 "--copy-metadata", dist_name,         # from _lib_copy_metadata
 "--add-data", "src;dest",             # per data folder
 preprocessed_script]
```

If the first run fails, PyX retries with `pyinstaller` (lowercase module name) as a fallback.

---

## Path Resolution Strategy

| Context | `_get_base_dir()` returns | `_resolve_packaged_path()` base |
|---------|--------------------------|----------------------------------|
| Running as `.py` script | Directory of the `.py` file | Same as above |
| Running as frozen `.exe` | Directory of the `.exe` | `sys._MEIPASS` (PyInstaller temp dir) |

`PyX_Data/` is always created adjacent to whatever `_get_base_dir()` returns.

---

## Thread Safety

All GUI mutations must occur on the main thread. The following patterns are used throughout:

- `self.after(0, lambda: widget.configure(...))` — schedule a GUI update from a background thread.
- `_log(message)` — appends to `log_lines` and schedules a `CTkTextbox` insert via `after(0, ...)`.
- `_set_status(text, colour)` and `_set_progress(value)` — both use `after(0, ...)`.

Never call Tkinter/customtkinter widget methods directly from a non-main thread.

---

## Adding a New Step

1. Create a new `ctk.CTkFrame` subclass following the pattern of existing step classes.
2. Add its label to `STEP_LABELS`.
3. Instantiate it in `Wizard.__init__` and append it to `self.steps`.
4. Update back/next navigation `go_to_step()` calls in adjacent steps.

---

## Constants Reference

| Constant | Value | Purpose |
|----------|-------|---------|
| `APP_VERSION` | `"BETA 0.28"` | Displayed in window title and build log header. |
| `DEFAULT_AUTHOR` | `"TRADELY.DEV"` | Written to manifest and displayed in Config step. |
| `PYINSTALLER_FLAGS` | `["--onefile", "--clean", "--noconfirm"]` | Base PyInstaller flags applied to every build. |
| `DEFAULT_ICON_URL` | `https://doc.tradely.dev/images/tradely.ico` | Fallback icon downloaded if the user provides none. |
| `SIGNTOOL_RELATIVE_PATH` | `signtool/signtool.exe` | Resolved via `_resolve_packaged_path()`. |
| `LIBRARIES_CATEGORY_FILE` | `https://doc.tradely.dev/PyX/lib_categories.json` | Remote library manifest URL. |

---

## Colour Scheme

All colours are defined as module-level constants with the prefix `COL_`. The theme is dark green.

| Constant | Hex | Use |
|----------|-----|-----|
| `COL_BG` | `#0a0f0a` | Main window background |
| `COL_PANEL` | `#0d1a0d` | Sidebar background |
| `COL_CARD` | `#111f11` | Card/panel background |
| `COL_ACCENT` | `#2d9e2d` | Primary buttons, progress bar |
| `COL_SUCCESS` | `#4ade80` | Completed steps, success messages |
| `COL_WARNING` | `#fbbf24` | Warnings |
| `COL_ERROR` | `#f87171` | Errors, validation failures |
| `COL_TEXT` | `#e8f5e8` | Primary text |
| `COL_MUTED` | `#5a7a5a` | Secondary/inactive text |

---

## Building PyX Itself

PyX is distributed as a PyInstaller-frozen executable. To rebuild the PyX binary:

```bash
pip install pyinstaller customtkinter cryptography
pyinstaller --onefile --clean --noconfirm --noconsole \
    --add-data "signtool;signtool" \
    --name PyX \
    PyX_V0_28_BETA.py
```

Ensure `signtool/signtool.exe` is present in the working directory before running the above command so it is bundled into the output.
