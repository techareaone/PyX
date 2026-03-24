# PyX Wizard — EXE Builder

> A [TRADELY](https://doc.tradely.dev) Project

PyX is a graphical wizard that packages Python scripts into standalone Windows executables. It automates virtual environment creation, dependency detection, PyInstaller orchestration, and optional code signing — all through a step-by-step GUI requiring no command-line interaction.

---

## Overview

PyX wraps [PyInstaller](https://pyinstaller.org) with a guided interface and adds several layers of automation that developers would otherwise handle manually:

- Isolated per-project virtual environments to avoid dependency conflicts between builds.
- AST-based import detection that scans the target script and installs only the third-party packages it actually uses.
- Automatic resolution of common PyInstaller pain points (`--collect-all`, `--hidden-import`, `--copy-metadata`) driven by a remotely maintained library manifest.
- A source-level preprocessor that injects a `_resolve_packaged_path()` helper and rewrites `"packaged-within-exe:<path>"` string literals so bundled resources resolve correctly at runtime whether the program is run as a script or as a frozen executable.
- Optional code signing via `signtool.exe` using a PFX/P12 certificate.
- Build logs and a JSON manifest written to every project directory.

---

## Distribution

PyX is distributed as a pre-built Windows executable. The repository release contains:

| File | Description |
|------|-------------|
| `PyX.exe` | The compiled application. Run this directly — no Python installation required on the end-user machine. |
| `PyX_V0_28_BETA.py` | The full source file included alongside the executable for transparency and developer reference. |
| `signtool/signtool.exe` | Microsoft SignTool, bundled for code-signing support. |

Output files from each build are placed under a `PyX_Data/` directory next to the executable.

---

## Requirements

**To run the PyX executable:** none. The executable is self-contained.

**To run the source file directly** (developer use):

- Python 3.10 or later
- `customtkinter` — `pip install customtkinter`
- `cryptography` *(optional, for PFX validation)* — `pip install cryptography`

**For builds to succeed on the target machine**, Python must be installed and available on `PATH`. PyX creates its own virtual environment and installs PyInstaller inside it; it does not use the system Python environment for anything other than bootstrapping.

---

## Project Structure

```
PyX.exe                        ← Distributed executable
PyX_V0_28_BETA.py              ← Source file
signtool/
    signtool.exe               ← Bundled Microsoft SignTool
PyX_Data/                      ← Created on first build
    <ProjectName>/
        venv/                  ← Isolated virtual environment
        build/                 ← PyInstaller intermediate files
        dist/                  ← Final executable output
        logs/                  ← Timestamped build logs
        pyx_manifest.json      ← Build metadata
```

---

## Wizard Steps

| Step | Name | Description |
|------|------|-------------|
| 0 | Welcome | Overview, antivirus guidance, feature summary. |
| 1 | Script | Select the `.py` file to build. Imports are detected and displayed. |
| 2 | Config | Set project name, console/GUI mode, and optional custom icon. |
| 3 | Data | Optionally bundle data folders into the executable. |
| 4 | Certificate | Optionally select a PFX/P12 certificate for code signing. |
| 5 | Build | Execute the build, view streaming logs, and open output. |

---

## Remote Library Manifest

At startup, PyX fetches `lib_categories.json` from `https://doc.tradely.dev/PyX/lib_categories.json`. This file drives:

- **Library categorisation** shown in the detected-imports panel.
- **`--collect-all`** flags for packages that use dynamic imports.
- **`--hidden-import`** lists for packages with C extensions or lazy loaders.
- **`--copy-metadata`** mappings for packages whose import name differs from their pip distribution name.

Updating this remote file pushes improvements to all existing installs without requiring a new executable release. If the fetch fails (no internet), PyX falls back to a hardcoded baseline set.

---

## Antivirus Considerations

PyInstaller-generated executables are frequently flagged as false positives by antivirus software. Users should add the following to their antivirus exclusions before building:

1. The folder containing the target script.
2. The target script file itself.
3. The `PyX_Data/` output directory.

---

## Code Signing

Code signing requires `signtool.exe` to be present at `signtool/signtool.exe` relative to the executable (already packaged in the distributed release). Signing uses SHA-256 with a DigiCert RFC 3161 timestamp server. Self-signed certificates are supported for testing but will not satisfy Windows SmartScreen for public distribution.

The `cryptography` package is required for PFX validation within the UI. If it is absent, validation is skipped but signing is still attempted at build time.

---

## License

© TRADELY.DEV. All rights reserved. Refer to the repository licence file for terms.
