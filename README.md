# PyX Wizard — EXE Builder

> A [TRADELY](https://doc.tradely.dev) Project

⚠️ **Warning:** The releases here are commonly flagged as malware due to their nature of operating with exes. We do not recommend you run unknown software on your device! We provide all python code of our program in the [Python Folder](python) .

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

PyX is distributed as a pre-built Windows executable in releases. It can also be used as a python library using `pip install pyxwizard`.

**For builds to succeed on the target machine**, Python must be installed and available on `PATH`. PyX creates its own virtual environment and installs PyInstaller inside it; it does not use the system Python environment for anything other than bootstrapping.

SignTool must be installed if signing certificates using the library. It comes pre-packaged with the EXE Wizard.

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

## Program Images

<img width="895" height="757" alt="image" src="https://github.com/user-attachments/assets/2901ae44-8494-4e3b-992b-9b5455f839ce" />
<img width="887" height="755" alt="image" src="https://github.com/user-attachments/assets/bc7d4c8f-d056-4e08-a5f9-d41f8426ca61" />
<img width="884" height="757" alt="image" src="https://github.com/user-attachments/assets/39558c9d-c028-4c27-a5d6-e98a190c17bb" />
<img width="881" height="752" alt="image" src="https://github.com/user-attachments/assets/edae0581-c825-4182-a734-f0e9806c43c7" />
<img width="882" height="752" alt="image" src="https://github.com/user-attachments/assets/7cb3b01a-fb96-4dfc-803a-9f210ee4fd3f" />
<img width="885" height="754" alt="image" src="https://github.com/user-attachments/assets/fd08acd0-9c94-4ed6-8610-81a892133dd7" />
<img width="887" height="393" alt="image" src="https://github.com/user-attachments/assets/a0b34b67-198d-4520-b541-fab3b2d92f53" />

---
## License

© TRADELY.DEV. All rights reserved. Refer to the repository licence file for terms.
