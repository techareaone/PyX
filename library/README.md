# PyX Wizard — Library Edition

**Python → EXE Builder**  
Package Python scripts into standalone Windows executables from code.

## Quick Start

```python
import pyxwizard as PyXWizard

PyXWizard.begin()
PyXWizard.location("my_script.py")
PyXWizard.name("MyApp")
PyXWizard.build()
```

## API Reference

| Command | Required | Default | Description |
|---|---|---|---|
| `PyXWizard.begin()` | Yes | — | Initialise PyX, fetch lib categories |
| `PyXWizard.location(path)` | Yes | — | Script path or `"self"` |
| `PyXWizard.name(name)` | Yes | — | Project name (= EXE filename) |
| `PyXWizard.author(name)` | No | `TRADELY.DEV` | Author metadata |
| `PyXWizard.console(bool)` | No | `True` | Show console window |
| `PyXWizard.icon(path)` | No | Tradely icon | Custom .ico file |
| `PyXWizard.data(f1, f2, ...)` | No | None | Folders to bundle |
| `PyXWizard.cert(pfx, pwd, signtool?)` | No | None | Code signing cert |
| `PyXWizard.outlocation(path)` | No | Script dir | Where to put PyX_Data |
| `PyXWizard.build()` | Yes | — | Run the build, returns exe Path |

---

## Notes

- **"self" mode**: `PyXWizard.location("self")` packages the calling script. All 
  `import pyx` and `PyXWizard.xxx()` lines are automatically removed from the 
  packaged copy.
- **Data folders**: Files in bundled folders are accessible at runtime with 
  `"packaged-within-exe:folder_name/file.ext"` string literals (auto-rewritten 
  by the preprocessor).
- **Venv reuse**: Building the same project name twice reuses the existing 
  virtual environment instead of recreating it.
- **Library categories**: On `begin()`, PyX fetches a remote JSON of known 
  library metadata to improve PyInstaller compatibility (collect-all, 
  hidden-imports, copy-metadata). Works offline too — just without 
  categorisation.

  ## Further Details

Check out [PyX Wizard by TRADELY](https://doc.tradely.dev)
PyPi Library available at: [PyPi PyXWizard](https://pypi.org/project/PyXWizard/)

Use the README there to set up the library.
